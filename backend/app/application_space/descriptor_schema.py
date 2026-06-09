from __future__ import annotations

from typing import List

from ..schemas import ApplicationNode


def descriptor_text(node: ApplicationNode) -> str:
    parts: List[str] = [
        node.label,
        node.application_text,
        node.domain,
        node.function,
        node.stimulus or "",
        node.response or "",
        node.operating_frequency_or_wavelength or "",
        node.device_type or "",
        node.device_architecture or "",
        node.physical_em_mechanism or "",
        node.material_class or "",
        " ".join(node.material_names),
        " ".join(node.em_property_requirements),
        " ".join(node.non_em_constraints),
    ]
    return " ".join(part for part in parts if part)
