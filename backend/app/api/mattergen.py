from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.mattergen_job_service import MatterGenJobService
from ..services.mattergen_setup_service import MatterGenSetupService
from .utils import raise_http

router = APIRouter(prefix="/mattergen", tags=["mattergen"])


@router.get("/status")
def status():
    return MatterGenSetupService().status()


@router.post("/setup-check")
def setup_check():
    return MatterGenSetupService().status()


@router.post("/jobs")
def create_job(pathway_id: str, db: Session = Depends(get_db)):
    try:
        return MatterGenJobService().create_job(db, pathway_id)
    except Exception as exc:
        raise_http(exc)


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    try:
        return MatterGenJobService().get(db, job_id)
    except Exception as exc:
        raise_http(exc)


@router.get("/jobs/{job_id}/candidates")
def candidates(job_id: str, db: Session = Depends(get_db)):
    try:
        return MatterGenJobService().candidates(db, job_id)
    except Exception as exc:
        raise_http(exc)
