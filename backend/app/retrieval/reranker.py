from __future__ import annotations

from typing import List

from ..schemas import EvidenceChunk


def rerank_by_evidence_strength(chunks: List[EvidenceChunk]) -> List[EvidenceChunk]:
    return sorted(
        chunks,
        key=lambda chunk: (chunk.relevance_score, 1 if chunk.doi else 0, chunk.year or 0),
        reverse=True,
    )
