from __future__ import annotations

from typing import List

from ..schemas import MatterGenDirectSupport, PropertyRequirement


SUPPORTED_PROXY_TERMS = {
    "band gap": "band gap",
    "formation energy": "stability/formation-energy proxy",
    "stability": "stability/formation-energy proxy",
    "magnetic": "magnetic density proxy",
    "bulk modulus": "bulk modulus",
}


def classify_mattergen_support(requirement: PropertyRequirement) -> PropertyRequirement:
    text = f"{requirement.property_name} {requirement.target_range_or_qualitative_requirement}".lower()
    if any(term in text for term in ["oxide", "nitride", "carbide", "chalcogenide", "ferrite"]):
        requirement.mattergen_direct_support = MatterGenDirectSupport.proxy_only
    for term in SUPPORTED_PROXY_TERMS:
        if term in text:
            requirement.mattergen_direct_support = MatterGenDirectSupport.supported
            return requirement
    if requirement.property_category in {"dielectric", "optical", "device_level"}:
        requirement.mattergen_direct_support = MatterGenDirectSupport.unsupported
    return requirement


def normalize_property_envelope(requirements: List[PropertyRequirement]) -> List[PropertyRequirement]:
    return [classify_mattergen_support(req) for req in requirements]
