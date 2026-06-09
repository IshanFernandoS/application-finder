from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from ..database import EvidenceRecord
from ..schemas import EvidenceChunk
from .bm25 import BM25Index


class HybridRetriever:
    def __init__(self, db: Session):
        self.db = db
        self.records = db.query(EvidenceRecord).all()
        self.chunks: Dict[str, EvidenceChunk] = {
            record.evidence_id: EvidenceChunk(**record.payload) for record in self.records
        }
        self.bm25 = BM25Index((chunk.evidence_id, chunk.text) for chunk in self.chunks.values())

    def search(self, query: str, top_k: int = 12) -> List[EvidenceChunk]:
        bm25_results = self.bm25.search(query, top_k=top_k)
        chunks: List[EvidenceChunk] = []
        max_score = max([score for _, score in bm25_results], default=1.0)
        for evidence_id, score in bm25_results:
            chunk = self.chunks[evidence_id]
            chunk.relevance_score = score / max_score if max_score else 0.0
            chunks.append(chunk)
        return chunks

    def search_many(self, queries: List[str], top_k: int = 20) -> List[EvidenceChunk]:
        seen: Dict[str, EvidenceChunk] = {}
        for query in queries:
            for chunk in self.search(query, top_k=top_k):
                current = seen.get(chunk.evidence_id)
                if current is None or chunk.relevance_score > current.relevance_score:
                    seen[chunk.evidence_id] = chunk
        return sorted(seen.values(), key=lambda item: item.relevance_score, reverse=True)[:top_k]
