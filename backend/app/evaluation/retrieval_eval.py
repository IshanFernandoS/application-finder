from __future__ import annotations

from typing import Dict, List

from ..schemas import EvidenceChunk


def retrieval_metrics(chunks: List[EvidenceChunk]) -> Dict[str, float]:
    if not chunks:
        return {"retrieval_relevance": 0.0, "citation_coverage": 0.0, "evidence_support_correctness": 0.0}
    citation_coverage = sum(1 for chunk in chunks if chunk.doi or chunk.source_path) / len(chunks)
    relevance = sum(chunk.relevance_score for chunk in chunks) / len(chunks)
    return {
        "retrieval_relevance": round(relevance, 4),
        "citation_coverage": round(citation_coverage, 4),
        "evidence_support_correctness": round(citation_coverage, 4),
    }
