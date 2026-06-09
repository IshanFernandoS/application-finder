from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..database import EvidenceRecord
from ..schemas import EvidenceChunk


class CitationStore:
    def __init__(self, db: Session):
        self.db = db

    def get(self, evidence_id: str) -> Optional[EvidenceChunk]:
        record = self.db.get(EvidenceRecord, evidence_id)
        return EvidenceChunk(**record.payload) if record else None

    def get_many(self, evidence_ids: List[str]) -> Dict[str, EvidenceChunk]:
        chunks: Dict[str, EvidenceChunk] = {}
        for evidence_id in evidence_ids:
            chunk = self.get(evidence_id)
            if chunk:
                chunks[evidence_id] = chunk
        return chunks
