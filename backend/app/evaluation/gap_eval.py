from __future__ import annotations

from typing import Dict, List

from ..schemas import Gap


def gap_metrics(gaps: List[Gap]) -> Dict[str, float]:
    if not gaps:
        return {
            "density_score": 0.0,
            "neighbour_diversity_score": 0.0,
            "boundary_evidence_score": 0.0,
            "feasibility_score": 0.0,
            "interpretability_score": 0.0,
            "uncertainty_score": 0.0,
        }
    return {
        "density_score": round(sum(gap.novelty_score for gap in gaps) / len(gaps), 4),
        "neighbour_diversity_score": round(sum(gap.neighbour_diversity_score for gap in gaps) / len(gaps), 4),
        "boundary_evidence_score": round(sum(gap.boundary_evidence_score for gap in gaps) / len(gaps), 4),
        "feasibility_score": round(sum(gap.feasibility_score for gap in gaps) / len(gaps), 4),
        "interpretability_score": round(sum(1 for gap in gaps if gap.pseudo_application_hypotheses) / len(gaps), 4),
        "uncertainty_score": round(sum(gap.uncertainty_score for gap in gaps) / len(gaps), 4),
    }
