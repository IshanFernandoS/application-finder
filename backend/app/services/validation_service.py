from __future__ import annotations

from typing import Dict

from sqlalchemy.orm import Session

from ..database import CandidateRecord
from ..schemas import MaterialCandidate, ValidationStatus
from .serialization import model_to_dict


class ValidationService:
    def validate_candidate(self, db: Session, candidate_id: str, status: ValidationStatus = ValidationStatus.unvalidated) -> Dict[str, object]:
        record = db.get(CandidateRecord, candidate_id)
        if not record:
            raise KeyError(candidate_id)
        candidate = MaterialCandidate(**record.payload)
        candidate.validation_status = status
        record.payload = model_to_dict(candidate)
        db.commit()
        return {
            "candidate_id": candidate_id,
            "validation_status": candidate.validation_status,
            "hooks": [
                "pymatgen structure parse",
                "composition sanity check",
                "Materials Project lookup placeholder",
                "dielectric property lookup placeholder",
                "optical constants database placeholder",
                "DFT workflow export placeholder",
                "CST/HFSS/COMSOL export placeholder",
                "user validation import",
            ],
        }
