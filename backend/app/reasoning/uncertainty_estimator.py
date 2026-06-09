from __future__ import annotations

from ..schemas import FBSPMPathway, MatterGenDirectSupport


def pathway_uncertainty_score(pathway: FBSPMPathway) -> float:
    evidence_count = len(set(pathway.evidence_ids))
    unsupported = sum(
        1 for req in pathway.material_property_envelope if req.mattergen_direct_support == MatterGenDirectSupport.unsupported
    )
    candidate_count = len(pathway.candidate_materials)
    score = 1.0 - min(0.75, evidence_count * 0.08 + candidate_count * 0.06) + min(0.25, unsupported * 0.04)
    return float(round(max(0.05, min(1.0, score)), 4))
