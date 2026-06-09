from __future__ import annotations

from typing import Dict, List

from ..schemas import ApplicationNode


def field_completion_rate(nodes: List[ApplicationNode]) -> float:
    fields = [
        "domain",
        "function",
        "operating_frequency_or_wavelength",
        "device_type",
        "physical_em_mechanism",
        "material_class",
        "em_property_requirements",
        "evidence_ids",
    ]
    if not nodes:
        return 0.0
    total = len(nodes) * len(fields)
    complete = 0
    for node in nodes:
        for field in fields:
            value = getattr(node, field)
            if value:
                complete += 1
    return complete / total


def descriptor_metrics(nodes: List[ApplicationNode]) -> Dict[str, float]:
    evidence_linked = sum(1 for node in nodes if node.evidence_ids)
    return {
        "field_completion_rate": round(field_completion_rate(nodes), 4),
        "evidence_sentence_link_rate": round(evidence_linked / max(len(nodes), 1), 4),
        "mean_confidence": round(sum(node.confidence for node in nodes) / max(len(nodes), 1), 4),
    }
