from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.fbs_pm_service import FBSPMService
from ..services.gap_characterization_service import GapCharacterizationService
from ..services.gap_detection_service import GapDetectionService
from ..services.rag_service import RAGService
from ..services.scope_service import ScopeService
from .utils import raise_http

router = APIRouter(prefix="/gaps", tags=["gaps"])


@router.post("/detect")
def detect(scope_id: str = "electromagnetic_functional_materials", db: Session = Depends(get_db)):
    try:
        scope = ScopeService().get_scope(db, scope_id)
        return GapDetectionService().detect(db, scope)
    except Exception as exc:
        raise_http(exc)


@router.get("")
def list_gaps(scope_id: str = "electromagnetic_functional_materials", db: Session = Depends(get_db)):
    return GapDetectionService().list(db, scope_id)


@router.get("/{gap_id}")
def get_gap(gap_id: str, db: Session = Depends(get_db)):
    try:
        return GapDetectionService().get(db, gap_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/{gap_id}/characterize")
def characterize(gap_id: str, db: Session = Depends(get_db)):
    try:
        return GapCharacterizationService().characterize(db, gap_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/{gap_id}/retrieve-evidence")
def retrieve_evidence(gap_id: str, db: Session = Depends(get_db)):
    try:
        return RAGService().retrieve_boundary_evidence(db, gap_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/{gap_id}/generate-pathways")
def generate_pathways(gap_id: str, scope_id: str = "electromagnetic_functional_materials", db: Session = Depends(get_db)):
    try:
        scope = ScopeService().get_scope(db, scope_id)
        return FBSPMService().generate_for_gap(db, scope, gap_id)
    except Exception as exc:
        raise_http(exc)
