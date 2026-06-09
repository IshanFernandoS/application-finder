from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..reasoning.constraint_translator import translate_constraints
from ..services.evidence_validation_service import EvidenceValidationService
from ..services.fbs_pm_service import FBSPMService
from ..services.pathway_ranking_service import PathwayRankingService
from .utils import raise_http

router = APIRouter(prefix="/pathways", tags=["pathways"])


@router.get("/{pathway_id}")
def get_pathway(pathway_id: str, db: Session = Depends(get_db)):
    try:
        return FBSPMService().get(db, pathway_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/{pathway_id}/validate-evidence")
def validate_evidence(pathway_id: str, db: Session = Depends(get_db)):
    try:
        return EvidenceValidationService().validate_pathway(db, pathway_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/{pathway_id}/rank")
def rank(pathway_id: str, db: Session = Depends(get_db)):
    try:
        return PathwayRankingService().rank(db, pathway_id)
    except Exception as exc:
        raise_http(exc)


@router.post("/{pathway_id}/mattergen/translate-constraints")
def translate(pathway_id: str, db: Session = Depends(get_db)):
    try:
        pathway = FBSPMService().get(db, pathway_id)
        constraints = translate_constraints(pathway)
        pathway.mattergen_constraints = constraints
        FBSPMService().update(db, pathway)
        return constraints
    except Exception as exc:
        raise_http(exc)
