from __future__ import annotations

from collections import Counter
from typing import Dict, List

from ..schemas import ApplicationNode


def summarize_boundary(nodes: List[ApplicationNode]) -> Dict[str, object]:
    def common(field: str) -> List[str]:
        values = [getattr(node, field) for node in nodes if getattr(node, field)]
        return [value for value, _ in Counter(values).most_common(5)]

    property_terms = Counter(term for node in nodes for term in node.em_property_requirements)
    return {
        "domains": common("domain"),
        "device_types": common("device_type"),
        "mechanisms": common("physical_em_mechanism"),
        "material_classes": common("material_class"),
        "property_requirements": [value for value, _ in property_terms.most_common(8)],
    }


def pseudo_application_from_boundary(boundary: Dict[str, object]) -> List[str]:
    domains = list(boundary.get("domains") or ["electromagnetic sensing"])
    devices = list(boundary.get("device_types") or ["adaptive device"])
    mechanisms = list(boundary.get("mechanisms") or ["frequency-dependent EM response"])
    materials = list(boundary.get("material_classes") or ["inorganic functional material"])
    return [
        f"{domains[0]} using {mechanisms[0]} in a {devices[0]} with {materials[0]}-class property tuning",
        f"Boundary application connecting {', '.join(domains[:2])} through {', '.join(mechanisms[:2])}",
    ]
