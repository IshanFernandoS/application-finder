from __future__ import annotations

from typing import Dict

from sqlalchemy.orm import Session

from ..exceptions import ConfigurationError
from ..schemas import BaselineRunRequest
from ..services.gap_detection_service import GapDetectionService
from ..services.rag_service import RAGService


class BaselineRunner:
    modes = {
        "baseline_direct_llm",
        "baseline_standard_rag",
        "baseline_nearest_neighbour",
        "baseline_fbs_pm_no_boundary_rag",
        "full_method",
    }

    def run(self, db: Session, request: BaselineRunRequest) -> Dict[str, object]:
        if request.mode not in self.modes:
            raise ConfigurationError(f"Unknown baseline mode: {request.mode}")
        if request.mode == "baseline_nearest_neighbour":
            if not request.gap_id:
                raise ConfigurationError("baseline_nearest_neighbour requires gap_id.")
            gap = GapDetectionService().get(db, request.gap_id)
            return {
                "mode": request.mode,
                "gap_id": gap.gap_id,
                "nearest_application_ids": gap.nearby_application_ids,
                "nearby_cluster_ids": gap.nearby_cluster_ids,
                "note": "Nearest-neighbour baseline uses only adjacent Application Space nodes.",
            }
        if request.mode == "baseline_standard_rag":
            query = request.query or request.gap_id or ""
            chunks = RAGService().retrieve_boundary_evidence(db, request.gap_id, top_k=12) if request.gap_id else []
            return {
                "mode": request.mode,
                "query": query,
                "evidence_ids": [chunk.evidence_id for chunk in chunks],
                "note": "Standard RAG evidence retrieved without FBS-PM pathway reasoning.",
            }
        if request.mode in {"baseline_direct_llm", "baseline_fbs_pm_no_boundary_rag"}:
            raise ConfigurationError(f"{request.mode} requires configured OpenAI reasoning and is not run as a fake fallback.")
        return {
            "mode": request.mode,
            "note": "Use the gap endpoints for boundary-RAG -> FBS-PM -> MatterGen -> validation full-method execution.",
        }
