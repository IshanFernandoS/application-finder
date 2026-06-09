from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.report_service import ReportService
from .utils import raise_http

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{gap_id}")
def generate(gap_id: str, db: Session = Depends(get_db)):
    try:
        return ReportService().generate(db, gap_id)
    except Exception as exc:
        raise_http(exc)


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    return ReportService().list(db)
