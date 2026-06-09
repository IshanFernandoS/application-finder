from __future__ import annotations

from typing import Dict, List

from ..schemas import FBSPMPathway


def fbs_pm_metrics(pathways: List[FBSPMPathway]) -> Dict[str, float]:
    if not pathways:
        return {
            "fbs_pm_completeness": 0.0,
            "no_direct_application_to_material_jump": 0.0,
            "property_envelope_measurability": 0.0,
            "uncertainty_quality": 0.0,
        }
    complete = 0
    no_jump = 0
    measurable = 0
    uncertainty = 0
    for pathway in pathways:
        if all(
            [
                pathway.function,
                pathway.behaviour_or_mechanism,
                pathway.structure_or_device_realization,
                pathway.material_property_envelope,
                pathway.candidate_materials,
            ]
        ):
            complete += 1
        if not (pathway.candidate_materials and not pathway.material_property_envelope):
            no_jump += 1
        if all(req.measurement_method_or_proxy or req.validation_method for req in pathway.material_property_envelope):
            measurable += 1
        if pathway.uncertainty:
            uncertainty += 1
    return {
        "fbs_pm_completeness": round(complete / len(pathways), 4),
        "no_direct_application_to_material_jump": round(no_jump / len(pathways), 4),
        "property_envelope_measurability": round(measurable / len(pathways), 4),
        "uncertainty_quality": round(uncertainty / len(pathways), 4),
    }
