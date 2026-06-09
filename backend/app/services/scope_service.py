from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..database import ScopeRecord
from ..schemas import Scope
from .serialization import model_to_dict


DEFAULT_EM_SCOPE = Scope(
    scope_id="electromagnetic_functional_materials",
    title="Electromagnetic Functional Materials and Devices",
    description=(
        "Literature-derived application space for materials used in RF, microwave, THz, "
        "infrared, optical, photonic, sensing, shielding, absorber, antenna, and adaptive "
        "electromagnetic device applications."
    ),
    included_domains=[
        "antennas and antenna substrates",
        "RF/microwave sensing",
        "wearable electromagnetic sensors",
        "non-invasive electromagnetic sensing",
        "metamaterials and metasurfaces",
        "absorbers",
        "radomes",
        "electromagnetic interference shielding",
        "frequency-selective surfaces",
        "tunable dielectrics",
        "tunable conductors",
        "phase-change electromagnetic materials",
        "plasmonic materials",
        "photonic coatings",
        "infrared and thermal-emissivity devices",
        "adaptive electromagnetic skins",
        "reconfigurable RF/THz/optical devices",
        "high-temperature electromagnetic materials",
        "electromagnetic thermal-barrier sensing",
        "communication, sensing, imaging, adaptive surfaces, and thermal/optical control",
    ],
    included_material_classes=[
        "oxides",
        "chalcogenides",
        "nitrides",
        "carbides",
        "ceramics",
        "ferrites",
        "ferroelectrics",
        "piezoelectrics",
        "magneto-dielectrics",
        "transparent conducting oxides",
        "phase-change inorganic materials",
        "plasmonic metals",
        "refractory plasmonic compounds",
        "MXenes and inorganic 2D materials",
        "conductive ceramics",
        "high-entropy ceramics",
        "high-entropy carbides",
        "high-entropy nitrides",
        "inorganic semiconductors",
    ],
    included_device_families=[
        "antenna substrate",
        "sensor",
        "metasurface",
        "absorber",
        "radome",
        "shielding layer",
        "frequency-selective surface",
        "photonic coating",
        "thermal-emissivity device",
        "reconfigurable device",
    ],
    included_mechanisms=[
        "dielectric polarization",
        "magnetic loss",
        "conductive loss",
        "plasmonic resonance",
        "phonon-polariton response",
        "impedance matching",
        "photonic interference",
        "phase transition",
        "ferroelectric tunability",
        "magneto-dielectric coupling",
    ],
    included_property_types=[
        "complex permittivity",
        "complex permeability",
        "loss tangent",
        "conductivity",
        "refractive index",
        "extinction coefficient",
        "emissivity",
        "band gap",
        "thermal stability",
        "oxidation resistance",
        "processability",
    ],
    excluded_domains=[
        "drug discovery",
        "purely mechanical product design",
        "circuit-only design without material-property relevance",
        "institutional login automation",
        "paywall bypassing",
    ],
    excluded_material_classes=[
        "pure polymer design unless linked to EM properties or composites",
        "purely biological systems unless the sensing route is electromagnetic",
    ],
    mattergen_compatibility_notes=[
        "MatterGen can target structure, chemistry, stability, band-gap and selected proxy properties.",
        "EM spectra, impedance matching, loss tangent, emissivity spectra and device-level resonances must remain validation requirements.",
    ],
    validation_methods=[
        "literature evidence audit",
        "DFT export",
        "EM simulation export for CST/HFSS/COMSOL",
        "optical constants lookup",
        "dielectric property lookup",
        "expert review",
    ],
    default_search_queries=[
        "electromagnetic functional materials RF microwave THz infrared optical photonic",
        "metamaterial metasurface absorber dielectric magnetic loss material property",
        "tunable dielectric phase change chalcogenide electromagnetic device",
        "high temperature electromagnetic materials thermal barrier sensing dielectric",
        "transparent conducting oxide plasmonic refractory optical coating emissivity",
    ],
    descriptor_weights={
        "physical_em_mechanism": 2.0,
        "device_type": 1.8,
        "operating_frequency_or_wavelength": 1.7,
        "em_property_requirements": 1.8,
        "function": 1.5,
        "material_class": 1.2,
        "operating_environment": 1.1,
    },
)


class ScopeService:
    def ensure_default_scope(self, db: Session) -> Scope:
        record = db.get(ScopeRecord, DEFAULT_EM_SCOPE.scope_id)
        if record:
            return Scope(**record.payload)
        record = ScopeRecord(scope_id=DEFAULT_EM_SCOPE.scope_id, payload=model_to_dict(DEFAULT_EM_SCOPE))
        db.add(record)
        db.commit()
        return DEFAULT_EM_SCOPE

    def list_scopes(self, db: Session) -> List[Scope]:
        self.ensure_default_scope(db)
        return [Scope(**record.payload) for record in db.query(ScopeRecord).order_by(ScopeRecord.scope_id).all()]

    def get_scope(self, db: Session, scope_id: str) -> Scope:
        self.ensure_default_scope(db)
        record = db.get(ScopeRecord, scope_id)
        if not record:
            raise KeyError(scope_id)
        return Scope(**record.payload)

    def upsert_scope(self, db: Session, scope: Scope) -> Scope:
        record = db.get(ScopeRecord, scope.scope_id)
        if record:
            record.payload = model_to_dict(scope)
        else:
            db.add(ScopeRecord(scope_id=scope.scope_id, payload=model_to_dict(scope)))
        db.commit()
        return scope
