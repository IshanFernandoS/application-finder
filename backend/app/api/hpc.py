from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import HPCJob, HPCJobCreateRequest
from ..services.analytics_service import AnalyticsService
from ..services.hpc_worker_service import HPCWorkerService
from .utils import raise_http

router = APIRouter(prefix="/hpc", tags=["hpc"])


def _auth(x_admin_api_key: Optional[str] = Header(default=None)):
    try:
        AnalyticsService().require_admin(x_admin_api_key)
    except Exception as exc:
        raise_http(exc)


@router.get("/status")
def status(_: None = Depends(_auth)):
    return HPCWorkerService().status()


@router.post("/check-connection")
def check_connection(_: None = Depends(_auth)):
    try:
        return HPCWorkerService().check_connection()
    except Exception as exc:
        raise_http(exc)


@router.post("/check-slurm")
def check_slurm(_: None = Depends(_auth)):
    try:
        return HPCWorkerService().check_slurm()
    except Exception as exc:
        raise_http(exc)


@router.post("/check-mattergen")
def check_mattergen(_: None = Depends(_auth)):
    try:
        return HPCWorkerService().check_mattergen()
    except Exception as exc:
        raise_http(exc)


@router.post("/jobs")
def create_job(request: HPCJobCreateRequest, _: None = Depends(_auth), db: Session = Depends(get_db)):
    try:
        return HPCWorkerService().create_job(db, request)
    except Exception as exc:
        raise_http(exc)


@router.get("/jobs")
def list_jobs(_: None = Depends(_auth), db: Session = Depends(get_db)):
    try:
        return HPCWorkerService().list_jobs(db)
    except Exception as exc:
        raise_http(exc)


@router.get("/jobs/{job_id}")
def get_job(job_id: str, _: None = Depends(_auth), db: Session = Depends(get_db)):
    try:
        return HPCWorkerService().get(db, job_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/jobs/{job_id}/poll")
def poll_job(job_id: str, _: None = Depends(_auth), db: Session = Depends(get_db)):
    try:
        return HPCWorkerService().poll(db, job_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/jobs/{job_id}/retrieve")
def retrieve_job(job_id: str, _: None = Depends(_auth), db: Session = Depends(get_db)):
    try:
        return HPCWorkerService().retrieve(db, job_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, _: None = Depends(_auth), db: Session = Depends(get_db)):
    try:
        return HPCWorkerService().cancel(db, job_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/jobs/{job_id}/worker-sync")
def worker_sync(job_id: str, update: HPCJob, _: None = Depends(_auth), db: Session = Depends(get_db)):
    try:
        return HPCWorkerService().worker_sync(db, job_id, update)
    except Exception as exc:
        raise_http(exc)
