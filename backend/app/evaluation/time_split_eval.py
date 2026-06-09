from __future__ import annotations

from typing import Dict, List

from ..schemas import ApplicationNode, FBSPMPathway


def time_split_support(pathways: List[FBSPMPathway], later_nodes: List[ApplicationNode]) -> Dict[str, float]:
    if not pathways:
        return {"time_split_validation_support": 0.0}
    later_text = " ".join(
        " ".join(
            [
                node.application_text,
                node.device_type or "",
                node.physical_em_mechanism or "",
                node.material_class or "",
                " ".join(node.material_names),
            ]
        ).lower()
        for node in later_nodes
    )
    supported = 0
    for pathway in pathways:
        terms = [
            pathway.function,
            pathway.behaviour_or_mechanism,
            pathway.structure_or_device_realization,
        ]
        if any(term.lower()[:40] in later_text for term in terms if term):
            supported += 1
    return {"time_split_validation_support": round(supported / len(pathways), 4)}
