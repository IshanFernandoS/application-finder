from __future__ import annotations

from typing import Dict, List

from ..schemas import FBSPMPathway


def validate_fbs_pm_chain(pathway: FBSPMPathway, available_evidence_ids: List[str]) -> Dict[str, object]:
    missing_fields = []
    for field in [
        "pseudo_application",
        "function",
        "behaviour_or_mechanism",
        "structure_or_device_realization",
        "material_property_envelope",
        "candidate_materials",
    ]:
        value = getattr(pathway, field)
        if not value:
            missing_fields.append(field)
    linked_evidence = set(pathway.evidence_ids)
    for req in pathway.material_property_envelope:
        linked_evidence.update(req.evidence_ids)
    for candidate in pathway.candidate_materials:
        linked_evidence.update(candidate.evidence_ids)
    unknown_evidence = sorted(eid for eid in linked_evidence if eid not in available_evidence_ids)
    direct_jump = bool(pathway.candidate_materials and not pathway.material_property_envelope)
    return {
        "valid": not missing_fields and not unknown_evidence and not direct_jump,
        "missing_fields": missing_fields,
        "unknown_evidence_ids": unknown_evidence,
        "direct_application_to_material_jump": direct_jump,
    }
