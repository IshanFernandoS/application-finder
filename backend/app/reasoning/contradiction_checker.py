from __future__ import annotations

from typing import List

from ..schemas import FBSPMPathway


def detect_basic_contradictions(pathway: FBSPMPathway) -> List[str]:
    contradictions: List[str] = []
    text = " ".join(
        req.target_range_or_qualitative_requirement.lower() for req in pathway.material_property_envelope
    )
    if "high conductivity" in text and "low loss dielectric" in text:
        contradictions.append("High conductivity and low-loss dielectric requirements may conflict in the same phase.")
    if "flexible" in text and "high-temperature" in text:
        contradictions.append("Flexibility and high-temperature stability need separate substrate/coating validation.")
    return contradictions
