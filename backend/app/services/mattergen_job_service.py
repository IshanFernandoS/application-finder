from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from ..config import settings
from ..database import MatterGenJobRecord
from ..reasoning.constraint_translator import translate_constraints
from ..schemas import MatterGenJob
from .fbs_pm_service import FBSPMService
from .ids import new_id
from .mattergen_setup_service import MatterGenSetupService
from .object_storage_service import ObjectStorageService
from .serialization import model_to_dict


class MatterGenJobService:
    def create_job(self, db: Session, pathway_id: str) -> MatterGenJob:
        pathway = FBSPMService().get(db, pathway_id)
        constraint_set = pathway.mattergen_constraints or translate_constraints(pathway)
        status = MatterGenSetupService().status()
        now = datetime.now(timezone.utc).isoformat()
        job_id = new_id("mgjob")
        output_dir = settings.output_dir / "mattergen" / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        object_storage = ObjectStorageService()
        output_ref = object_storage.storage_uri(f"mattergen/{job_id}/") if object_storage.enabled else str(output_dir)
        job_status = "queued" if status.status == "available" else "setup_needed"
        warnings = [] if status.status == "available" else status.details
        job = MatterGenJob(
            job_id=job_id,
            pathway_id=pathway_id,
            status=job_status,
            constraint_set=constraint_set,
            output_dir=output_ref,
            created_at=now,
            updated_at=now,
            candidates=[],
            warnings=warnings + ["Generated candidates are unvalidated until validation hooks pass."],
        )
        db.add(MatterGenJobRecord(job_id=job_id, pathway_id=pathway_id, status=job.status, payload=model_to_dict(job)))
        db.commit()
        return job

    def get(self, db: Session, job_id: str) -> MatterGenJob:
        record = db.get(MatterGenJobRecord, job_id)
        if not record:
            raise KeyError(job_id)
        return MatterGenJob(**record.payload)

    def candidates(self, db: Session, job_id: str) -> List:
        return self.get(db, job_id).candidates
