from __future__ import annotations

from typing import Dict

from sqlalchemy.orm import Session

from .fbs_pm_service import FBSPMService


class PathwayRankingService:
    def rank(self, db: Session, pathway_id: str) -> Dict[str, float]:
        pathway = FBSPMService().get(db, pathway_id)
        completeness = 1.0 if pathway.material_property_envelope and pathway.candidate_materials else 0.0
        evidence = min(1.0, len(set(pathway.evidence_ids)) / 8.0)
        uncertainty = pathway.scores.get("uncertainty", 0.5)
        contradiction_penalty = min(0.4, len(pathway.contradictions) * 0.12)
        direct_jump_penalty = 0.5 if pathway.candidate_materials and not pathway.material_property_envelope else 0.0
        overall = max(0.0, 0.35 * completeness + 0.35 * evidence + 0.3 * (1.0 - uncertainty) - contradiction_penalty - direct_jump_penalty)
        scores = {
            "completeness": round(completeness, 4),
            "evidence_support": round(evidence, 4),
            "uncertainty_quality": round(1.0 - uncertainty, 4),
            "contradiction_penalty": round(contradiction_penalty, 4),
            "direct_jump_penalty": round(direct_jump_penalty, 4),
            "overall": round(overall, 4),
        }
        pathway.scores.update(scores)
        FBSPMService().update(db, pathway)
        return scores
