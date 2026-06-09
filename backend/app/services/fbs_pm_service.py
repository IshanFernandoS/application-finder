from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..database import PathwayRecord
from ..reasoning.contradiction_checker import detect_basic_contradictions
from ..reasoning.constraint_translator import translate_constraints
from ..reasoning.evidence_validator import validate_fbs_pm_chain
from ..reasoning.fbs_pm_generator import FBSPMGenerator
from ..reasoning.uncertainty_estimator import pathway_uncertainty_score
from ..schemas import FBSPMPathway, Scope, ValidationStatus
from .gap_detection_service import GapDetectionService
from .rag_service import RAGService
from .serialization import model_to_dict


class FBSPMService:
    def generate_for_gap(self, db: Session, scope: Scope, gap_id: str) -> List[FBSPMPathway]:
        gap = GapDetectionService().get(db, gap_id)
        evidence = RAGService().retrieve_boundary_evidence(db, gap_id, top_k=24)
        pathways = FBSPMGenerator().generate(scope, gap, evidence)
        evidence_ids = [chunk.evidence_id for chunk in evidence]
        for pathway in pathways:
            pathway.contradictions.extend(detect_basic_contradictions(pathway))
            pathway.mattergen_constraints = translate_constraints(pathway)
            validation = validate_fbs_pm_chain(pathway, evidence_ids)
            pathway.scores["uncertainty"] = pathway_uncertainty_score(pathway)
            pathway.scores["evidence_link_validity"] = 1.0 if not validation["unknown_evidence_ids"] else 0.0
            pathway.scores["fbs_pm_complete"] = 0.0 if validation["missing_fields"] else 1.0
            if validation["valid"]:
                pathway.validation_status = ValidationStatus.literature_supported
            record = db.get(PathwayRecord, pathway.pathway_id)
            if record:
                record.payload = model_to_dict(pathway)
            else:
                db.add(PathwayRecord(pathway_id=pathway.pathway_id, gap_id=gap_id, payload=model_to_dict(pathway)))
        db.commit()
        return pathways

    def get(self, db: Session, pathway_id: str) -> FBSPMPathway:
        record = db.get(PathwayRecord, pathway_id)
        if not record:
            raise KeyError(pathway_id)
        return FBSPMPathway(**record.payload)

    def list_for_gap(self, db: Session, gap_id: str) -> List[FBSPMPathway]:
        return [FBSPMPathway(**record.payload) for record in db.query(PathwayRecord).filter(PathwayRecord.gap_id == gap_id)]

    def update(self, db: Session, pathway: FBSPMPathway) -> FBSPMPathway:
        record = db.get(PathwayRecord, pathway.pathway_id)
        if not record:
            raise KeyError(pathway.pathway_id)
        record.payload = model_to_dict(pathway)
        db.commit()
        return pathway
