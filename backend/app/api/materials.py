from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.material_candidate_service import MaterialCandidateService
from .utils import raise_http

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("/pathways/{pathway_id}/retrieve-candidates")
def retrieve_candidates(pathway_id: str, db: Session = Depends(get_db)):
    try:
        return MaterialCandidateService().retrieve_known_candidates(db, pathway_id)
    except Exception as exc:
        raise_http(exc)
