from __future__ import annotations

from typing import Dict, List

from ..schemas import FBSPMPathway, MatterGenConstraintSet, MatterGenDirectSupport, PropertyRequirement
from .em_property_extractor import normalize_property_envelope


MATERIAL_CLASS_CONSTRAINTS = {
    "oxide": {"chemistry_family": "oxide", "include_elements": ["O"]},
    "nitride": {"chemistry_family": "nitride", "include_elements": ["N"]},
    "carbide": {"chemistry_family": "carbide", "include_elements": ["C"]},
    "chalcogenide": {"chemistry_family": "chalcogenide", "include_elements": ["S", "Se", "Te"]},
    "ferrite": {"chemistry_family": "ferrite", "include_elements": ["Fe", "O"]},
    "ceramic": {"chemistry_family": "ceramic"},
}


def translate_constraints(pathway: FBSPMPathway) -> MatterGenConstraintSet:
    requirements = normalize_property_envelope(pathway.material_property_envelope)
    compatible: Dict[str, object] = {}
    unsupported: List[PropertyRequirement] = []
    for candidate in pathway.candidate_materials:
        key = candidate.material_class.lower()
        for material_key, constraints in MATERIAL_CLASS_CONSTRAINTS.items():
            if material_key in key:
                compatible.update(constraints)
    for requirement in requirements:
        text = f"{requirement.property_name} {requirement.target_range_or_qualitative_requirement}".lower()
        if requirement.mattergen_direct_support == MatterGenDirectSupport.unsupported:
            unsupported.append(requirement)
        elif "band gap" in text:
            compatible["band_gap"] = requirement.target_range_or_qualitative_requirement
        elif "bulk modulus" in text:
            compatible["bulk_modulus"] = requirement.target_range_or_qualitative_requirement
        elif "magnetic" in text:
            compatible["magnetic_density"] = requirement.target_range_or_qualitative_requirement
        elif "stability" in text or "formation" in text:
            compatible["stability_or_formation_energy"] = requirement.target_range_or_qualitative_requirement
        else:
            unsupported.append(requirement)
    score = len(compatible) / max(len(compatible) + len(unsupported), 1)
    return MatterGenConstraintSet(
        pathway_id=pathway.pathway_id,
        compatible_constraints=compatible,
        unsupported_em_properties=unsupported,
        compatibility_score=float(round(score, 4)),
        notes=[
            "Unsupported EM properties are retained as validation requirements.",
            "MatterGen outputs must be validated before scientific use.",
        ],
    )
