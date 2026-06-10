#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

sys.path.insert(0, str(ROOT))

from backend.app.reasoning.constraint_translator import translate_constraints  # noqa: E402
from backend.app.schemas import FBSPMPathway, HPCJob, HPCJobStatus, HPCJobType  # noqa: E402
from backend.app.services.hpc_slurm_service import HPCSlurmService  # noqa: E402


DEFAULT_REMOTE_URL = "https://application-finder-backend.onrender.com"
ACTIVE_STATES = {
    HPCJobStatus.submitted,
    HPCJobStatus.queued,
    HPCJobStatus.running,
    HPCJobStatus.retrieving_outputs,
}


class RemoteAPI:
    def __init__(self, base_url: str, admin_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.admin_key = admin_key

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, body: Any | None = None) -> Any:
        return self._request("POST", path, body)

    def _request(self, method: str, path: str, body: Any | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(f"{self.base_url}{path}", method=method, data=data)
        request.add_header("x-admin-api-key", self.admin_key)
        if data is not None:
            request.add_header("content-type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"{method} {path} failed with {exc.code}: {detail}") from exc


class LocalHPCRelay:
    def __init__(self, remote: RemoteAPI, dry_run: bool = False) -> None:
        self.remote = remote
        self.slurm = HPCSlurmService()
        self.dry_run = dry_run

    def run_once(self) -> None:
        jobs = [HPCJob(**item) for item in self.remote.get("/api/hpc/jobs")]
        for job in jobs:
            if job.status == HPCJobStatus.queued and job.metadata.get("relay_mode") == "local_worker" and not job.slurm_job_id:
                self.submit(job)
            elif job.status in ACTIVE_STATES and job.slurm_job_id:
                self.poll_or_retrieve(job)

    def submit(self, job: HPCJob) -> None:
        local_workdir = self.local_workdir(job)
        local_workdir.mkdir(parents=True, exist_ok=True)
        try:
            job.status = HPCJobStatus.transferring_inputs
            job.local_workdir = str(local_workdir)
            self.sync(job)
            input_path = self.write_input(job, local_workdir)
            slurm_path = local_workdir / "job.slurm"
            slurm_path.write_text(self.slurm.render_slurm_script(job), encoding="utf-8")
            if self.dry_run:
                job.status = HPCJobStatus.submitted
                job.metadata["dry_run"] = True
            else:
                job = self.slurm.submit(job, local_workdir, input_path, slurm_path)
            self.sync(job)
        except Exception as exc:
            if self.is_auth_error(exc):
                job.status = HPCJobStatus.queued
                job.error = (
                    "Local relay is waiting for an authenticated SSH session. "
                    "Start scripts/hpc/start_control_master.sh, then the relay will retry this queued job."
                )
            else:
                job.status = HPCJobStatus.failed
                job.error = str(exc)
            self.sync(job)

    def poll_or_retrieve(self, job: HPCJob) -> None:
        local_workdir = self.local_workdir(job)
        try:
            job = self.slurm.poll(job)
            self.sync(job)
            if job.status == HPCJobStatus.completed:
                job.status = HPCJobStatus.retrieving_outputs
                self.sync(job)
                job = self.slurm.retrieve(job, local_workdir)
                self.sync(job)
        except Exception as exc:
            if self.is_auth_error(exc):
                job.error = (
                    "Local relay could not authenticate to HPC while polling. "
                    "Refresh the SSH control master, then the relay will retry."
                )
            else:
                job.status = HPCJobStatus.failed
                job.error = str(exc)
            self.sync(job)

    def write_input(self, job: HPCJob, local_workdir: Path) -> Path:
        payload: Dict[str, Any] = {
            "job_id": job.job_id,
            "job_type": job.job_type.value,
            "pathway_id": job.pathway_id,
            "payload": job.metadata.get("payload") or {},
            "created_by": "Application Finder local HPC relay",
        }
        if job.job_type == HPCJobType.mattergen_generation:
            if not job.pathway_id:
                raise RuntimeError("MatterGen generation jobs require pathway_id.")
            pathway_payload = self.remote.get(f"/api/pathways/{job.pathway_id}")
            pathway = FBSPMPathway(**pathway_payload)
            constraint_set = pathway.mattergen_constraints or translate_constraints(pathway)
            payload["pathway"] = pathway.model_dump(mode="json")
            payload["constraint_set"] = constraint_set.model_dump(mode="json")
        input_path = local_workdir / "input.json"
        input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return input_path

    def sync(self, job: HPCJob) -> None:
        self.remote.post(f"/api/hpc/jobs/{job.job_id}/worker-sync", job.model_dump(mode="json"))

    def local_workdir(self, job: HPCJob) -> Path:
        return ROOT / "outputs" / "hpc_jobs" / job.job_id

    def is_auth_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "permission denied" in message or "publickey" in message or "password" in message


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit Render-queued Application Finder HPC jobs from this Mac using the local SSH agent/keychain.")
    parser.add_argument("--remote-url", default=os.getenv("AF_REMOTE_BACKEND_URL", DEFAULT_REMOTE_URL))
    parser.add_argument("--admin-key", default=os.getenv("ADMIN_API_KEY"))
    parser.add_argument("--interval", type=int, default=int(os.getenv("AF_HPC_RELAY_INTERVAL", "30")))
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.admin_key:
        raise SystemExit("ADMIN_API_KEY is required in the environment or .env for the local HPC relay.")

    relay = LocalHPCRelay(RemoteAPI(args.remote_url, args.admin_key), dry_run=args.dry_run)
    print("Application Finder local HPC relay is polling for queued jobs.", flush=True)
    while True:
        try:
            relay.run_once()
        except Exception as exc:
            print(f"Local HPC relay cycle failed: {exc}", file=sys.stderr, flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
