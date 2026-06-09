from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..database import GapRecord
from ..schemas import EvidenceChunk, Gap
from ..retrieval.hybrid_retriever import HybridRetriever
from ..retrieval.reranker import rerank_by_evidence_strength
from .query_planner_service import QueryPlannerService


class RAGService:
    def retrieve_boundary_evidence(self, db: Session, gap_id: str, top_k: int = 20) -> List[EvidenceChunk]:
        record = db.get(GapRecord, gap_id)
        if not record:
            raise KeyError(gap_id)
        gap = Gap(**record.payload)
        queries = QueryPlannerService().boundary_queries(gap)
        chunks = HybridRetriever(db).search_many(queries, top_k=top_k)
        return rerank_by_evidence_strength(chunks)
