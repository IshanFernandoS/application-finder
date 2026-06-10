from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from ..config import settings
from ..database import CandidateRecord, HPCJobRecord
from ..exceptions import ConfigurationError
from ..reasoning.constraint_translator import translate_constraints
from ..schemas import (
    HPCCheckResult,
    HPCJob,
    HPCJobCreateRequest,
    HPCJobStatus,
    HPCJobType,
    HPCStatus,
    MaterialCandidate,
    ValidationStatus,
)
from .fbs_pm_service import FBSPMService
from .hpc_slurm_service import HPCSlurmService
from .ids import new_id, stable_id
from .serialization import model_to_dict


class HPCWorkerService:
    def __init__(self) -> None:
        self.slurm = HPCSlurmService()

    def status(self) -> HPCStatus:
        warnings = []
        if not settings.hpc_enabled:
            warnings.append("HPC worker is disabled. Set HPC_ENABLED=true to enable admin-only SSH/Slurm actions.")
        if settings.hpc_enabled and not settings.hpc_workdir:
            warnings.append("HPC_WORKDIR is required before jobs can be submitted.")
        safe_auth = bool(settings.hpc_ssh_key_path or settings.hpc_ssh_control_path or os.environ.get("SSH_AUTH_SOCK"))
        if settings.hpc_enabled and not safe_auth:
            if settings.hpc_queue_only:
                warnings.append("HPC queue-only relay mode is enabled. A local worker must submit queued jobs with SSH agent or keychain access.")
            else:
                warnings.append("Configure SSH agent forwarding, HPC_SSH_KEY_PATH, or HPC_SSH_CONTROL_PATH. Password automation is not supported.")
        return HPCStatus(
            enabled=settings.hpc_enabled,
            configured=settings.hpc_configured,
            mode=settings.hpc_mode,
            queue_only=settings.hpc_queue_only,
            safe_authentication=safe_auth,
            host_configured=bool(settings.hpc_host),
            username_configured=bool(settings.hpc_username),
            workdir_configured=bool(settings.hpc_workdir),
            ssh_key_configured=bool(settings.hpc_ssh_key_path),
            ssh_agent_available=bool(os.environ.get("SSH_AUTH_SOCK")),
            strict_host_key_checking=settings.hpc_strict_host_key_checking,
            scheduler_configured=settings.hpc_mode == "slurm_ssh",
            mattergen_hpc_env_configured=bool(settings.hpc_mattergen_env),
            supported_job_types=list(HPCJobType),
            warnings=warnings,
        )

    def check_connection(self) -> HPCCheckResult:
        return self.slurm.check_connection()

    def check_slurm(self) -> HPCCheckResult:
        return self.slurm.check_slurm()

    def check_mattergen(self) -> HPCCheckResult:
        return self.slurm.check_mattergen()

    def create_job(self, db: Session, request: HPCJobCreateRequest) -> HPCJob:
        self.slurm.require_configured()
        if request.job_type == HPCJobType.mattergen_generation and not request.pathway_id:
            raise ConfigurationError("MatterGen generation on HPC requires an FBS-PM pathway_id; gap-only submission is not allowed.")

        now = datetime.now(timezone.utc).isoformat()
        job_id = new_id("hpcjob")
        local_workdir = settings.output_dir / "hpc_jobs" / job_id
        local_workdir.mkdir(parents=True, exist_ok=True)
        job = HPCJob(
            job_id=job_id,
            job_type=request.job_type,
            status=HPCJobStatus.created,
            pathway_id=request.pathway_id,
            created_at=now,
            updated_at=now,
            local_workdir=str(local_workdir),
            metadata={"payload": request.payload},
        )
        self._save(db, job)
        if settings.hpc_queue_only:
            job.status = HPCJobStatus.queued
            job.metadata["relay_mode"] = "local_worker"
            job.metadata["payload"] = request.payload
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._save(db, job)
            return job
        try:
            job.status = HPCJobStatus.transferring_inputs
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._save(db, job)
            input_path = self._write_input(db, job, request, local_workdir)
            slurm_path = local_workdir / "job.slurm"
            slurm_path.write_text(self.slurm.render_slurm_script(job), encoding="utf-8")
            job = self.slurm.submit(job, local_workdir, input_path, slurm_path)
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._save(db, job)
            return job
        except Exception as exc:
            job.status = HPCJobStatus.failed
            job.error = str(exc)
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._save(db, job)
            raise

    def list_jobs(self, db: Session, limit: int = 25) -> List[HPCJob]:
        records = db.query(HPCJobRecord).order_by(HPCJobRecord.created_at.desc()).limit(limit).all()
        return [HPCJob(**record.payload) for record in records]

    def get(self, db: Session, job_id: str) -> HPCJob:
        record = db.get(HPCJobRecord, job_id)
        if not record:
            raise KeyError(job_id)
        return HPCJob(**record.payload)

    def poll(self, db: Session, job_id: str) -> HPCJob:
        job = self.get(db, job_id)
        job = self.slurm.poll(job)
        job.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(db, job)
        return job

    def retrieve(self, db: Session, job_id: str) -> HPCJob:
        job = self.get(db, job_id)
        job.status = HPCJobStatus.retrieving_outputs
        job.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(db, job)
        local_workdir = Path(job.local_workdir or settings.output_dir / "hpc_jobs" / job.job_id)
        job = self.slurm.retrieve(job, local_workdir)
        job.candidates = self._parse_candidates(db, job, local_workdir)
        job.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(db, job)
        return job

    def cancel(self, db: Session, job_id: str) -> HPCJob:
        job = self.get(db, job_id)
        job = self.slurm.cancel(job)
        job.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(db, job)
        return job

    def worker_sync(self, db: Session, job_id: str, update: HPCJob) -> HPCJob:
        if update.job_id != job_id:
            raise ConfigurationError("Worker update job_id does not match the URL job_id.")
        existing = self.get(db, job_id)
        existing.status = update.status
        existing.slurm_job_id = update.slurm_job_id
        existing.input_ref = update.input_ref
        existing.remote_workdir = update.remote_workdir
        existing.output_ref = update.output_ref
        existing.log_excerpt = update.log_excerpt
        existing.output_files = update.output_files
        existing.candidates = update.candidates
        existing.error = update.error
        existing.metadata.update(update.metadata or {})
        existing.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(db, existing)
        return existing

    def _write_input(self, db: Session, job: HPCJob, request: HPCJobCreateRequest, local_workdir: Path) -> Path:
        payload = {
            "job_id": job.job_id,
            "job_type": job.job_type.value,
            "pathway_id": job.pathway_id,
            "payload": request.payload,
            "created_by": "Application Finder",
        }
        if request.job_type == HPCJobType.mattergen_generation:
            pathway = FBSPMService().get(db, request.pathway_id or "")
            constraint_set = pathway.mattergen_constraints or translate_constraints(pathway)
            payload["pathway"] = model_to_dict(pathway)
            payload["constraint_set"] = model_to_dict(constraint_set)
        input_path = local_workdir / "input.json"
        input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return input_path

    def _parse_candidates(self, db: Session, job: HPCJob, local_workdir: Path) -> List[MaterialCandidate]:
        if job.job_type != HPCJobType.mattergen_generation or not job.pathway_id:
            return []
        output_dir = local_workdir / "outputs"
        structure_files = sorted(
            path for path in output_dir.glob("**/*") if path.is_file() and path.suffix.lower() in {".cif", ".json", ".xyz", ".vasp"}
        )
        candidates = []
        for path in structure_files[:100]:
            if path.name.startswith("application_finder_"):
                continue
            candidate = MaterialCandidate(
                candidate_id=stable_id("cand", job.job_id, str(path.relative_to(output_dir))),
                material=path.stem,
                material_class="generated structure",
                role_in_device="MatterGen-generated candidate for FBS-PM pathway validation",
                matched_em_properties=[],
                missing_or_uncertain_properties=["EM properties require downstream validation."],
                evidence_ids=[],
                evidence_strength=0.0,
                validation_status=ValidationStatus.unvalidated,
                source="hpc_mattergen",
                confidence=0.2,
                next_validation_step="Run DFT/property prediction and EM simulation validation hooks.",
            )
            candidates.append(candidate)
            db.merge(CandidateRecord(candidate_id=candidate.candidate_id, pathway_id=job.pathway_id, payload=model_to_dict(candidate)))
        db.commit()
        return candidates

    def _save(self, db: Session, job: HPCJob) -> None:
        db.merge(
            HPCJobRecord(
                job_id=job.job_id,
                job_type=job.job_type.value,
                status=job.status.value,
                pathway_id=job.pathway_id,
                slurm_job_id=job.slurm_job_id,
                payload=model_to_dict(job),
            )
        )
        db.commit()
