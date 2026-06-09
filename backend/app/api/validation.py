from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ValidationStatus
from ..services.validation_service import ValidationService
from .utils import raise_http

router = APIRouter(prefix="/candidates", tags=["validation"])


@router.post("/{candidate_id}/validate")
def validate_candidate(candidate_id: str, status: ValidationStatus = ValidationStatus.unvalidated, db: Session = Depends(get_db)):
    try:
        return ValidationService().validate_candidate(db, candidate_id, status=status)
    except Exception as exc:
        raise_http(exc)
