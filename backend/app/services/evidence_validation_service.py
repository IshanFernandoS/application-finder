from __future__ import annotations

from typing import Dict

from sqlalchemy.orm import Session

from ..database import EvidenceRecord
from ..reasoning.evidence_validator import validate_fbs_pm_chain
from .fbs_pm_service import FBSPMService


class EvidenceValidationService:
    def validate_pathway(self, db: Session, pathway_id: str) -> Dict[str, object]:
        pathway = FBSPMService().get(db, pathway_id)
        evidence_ids = [record.evidence_id for record in db.query(EvidenceRecord).all()]
        result = validate_fbs_pm_chain(pathway, evidence_ids)
        pathway.scores["evidence_validation"] = 1.0 if result["valid"] else 0.0
        FBSPMService().update(db, pathway)
        return result
