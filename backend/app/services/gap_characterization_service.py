from __future__ import annotations

from sqlalchemy.orm import Session

from ..schemas import Gap
from .gap_detection_service import GapDetectionService


class GapCharacterizationService:
    def characterize(self, db: Session, gap_id: str) -> Gap:
        return GapDetectionService().characterize(db, gap_id)
