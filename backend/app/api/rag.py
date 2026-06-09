from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..retrieval.hybrid_retriever import HybridRetriever

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/search")
def search(query: str, top_k: int = 12, db: Session = Depends(get_db)):
    return HybridRetriever(db).search(query, top_k=top_k)
