from __future__ import annotations

import re
from typing import List

from sqlalchemy.orm import Session

from ..database import ApplicationNodeRecord, CandidateRecord, EvidenceRecord
from ..schemas import MaterialCandidate, ValidationStatus
from .fbs_pm_service import FBSPMService
from .ids import stable_id
from .serialization import model_to_dict


MATERIAL_RE = re.compile(r"\b(?:TiO2|BaTiO3|VO2|GST|ITO|AZO|SiC|AlN|BN|MXene|Ti3C2|ferrite|perovskite|graphene)\b", re.I)


class MaterialCandidateService:
    def retrieve_known_candidates(self, db: Session, pathway_id: str) -> List[MaterialCandidate]:
        pathway = FBSPMService().get(db, pathway_id)
        candidates = {candidate.candidate_id: candidate for candidate in pathway.candidate_materials}
        text_requirements = [req.property_name for req in pathway.material_property_envelope]
        for node_record in db.query(ApplicationNodeRecord).all():
            node = node_record.payload
            for material in node.get("material_names", []):
                candidate = MaterialCandidate(
                    candidate_id=stable_id("cand", pathway_id, material, node.get("material_class")),
                    material=material,
                    material_class=node.get("material_class") or "unknown",
                    role_in_device=node.get("device_type") or pathway.structure_or_device_realization,
                    matched_em_properties=text_requirements,
                    missing_or_uncertain_properties=[],
                    evidence_ids=node.get("evidence_ids", []),
                    evidence_strength=min(1.0, len(node.get("evidence_ids", [])) / 4.0),
                    validation_status=ValidationStatus.literature_supported,
                    source="literature",
                    confidence=float(node.get("confidence") or 0.5),
                    next_validation_step="Check frequency-dependent EM properties against the pathway envelope.",
                )
                candidates[candidate.candidate_id] = candidate
        for evidence_record in db.query(EvidenceRecord).limit(500):
            for match in MATERIAL_RE.findall(evidence_record.text):
                material = match
                candidate = MaterialCandidate(
                    candidate_id=stable_id("cand", pathway_id, material, evidence_record.evidence_id),
                    material=material,
                    material_class="literature-mentioned",
                    role_in_device=pathway.structure_or_device_realization,
                    matched_em_properties=[],
                    missing_or_uncertain_properties=text_requirements,
                    evidence_ids=[evidence_record.evidence_id],
                    evidence_strength=0.35,
                    validation_status=ValidationStatus.unvalidated,
                    source="literature",
                    confidence=0.35,
                    next_validation_step="Extract and verify EM properties from cited source.",
                )
                candidates[candidate.candidate_id] = candidate
        pathway.candidate_materials = list(candidates.values())
        FBSPMService().update(db, pathway)
        for candidate in pathway.candidate_materials:
            record = db.get(CandidateRecord, candidate.candidate_id)
            if record:
                record.payload = model_to_dict(candidate)
            else:
                db.add(CandidateRecord(candidate_id=candidate.candidate_id, pathway_id=pathway_id, payload=model_to_dict(candidate)))
        db.commit()
        return pathway.candidate_materials
