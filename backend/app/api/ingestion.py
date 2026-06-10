from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas import DescriptorExtractionRequest, LiteratureIngestAndExtractRequest, LiteratureIngestRequest, LiteratureSearchRequest
from ..services.descriptor_extraction_service import DescriptorExtractionService
from ..services.ingestion_service import IngestionService
from ..services.object_storage_service import ObjectStorageService
from ..services.scope_service import ScopeService
from .utils import raise_http

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/files")
async def ingest_files(files: Optional[List[UploadFile]] = File(default=None), db: Session = Depends(get_db)):
    try:
        object_storage = ObjectStorageService()
        for upload in files or []:
            suffix = Path(upload.filename or "").suffix.lower()
            filename = Path(upload.filename or "upload").name
            if suffix == ".pdf":
                target = settings.data_dir / "pdfs" / filename
                object_path = f"uploads/pdfs/{filename}"
            elif suffix in {".txt", ".md", ".markdown"}:
                target = settings.data_dir / "evidence" / filename
                object_path = f"uploads/evidence/{filename}"
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
            target.parent.mkdir(parents=True, exist_ok=True)
            content = await upload.read()
            target.write_bytes(content)
            object_storage.upload_bytes(content, object_path, upload.content_type or "application/octet-stream")
        return IngestionService().ingest_local(db)
    except HTTPException:
        raise
    except Exception as exc:
        raise_http(exc)


@router.post("/zotero")
def ingest_zotero(db: Session = Depends(get_db)):
    try:
        return IngestionService().ingest_zotero(db)
    except Exception as exc:
        raise_http(exc)


@router.post("/public-search")
def public_search(request: LiteratureSearchRequest | None = Body(default=None), query: str = "", limit: int = 10):
    try:
        if request:
            query = request.query
            limit = request.limit
        if not query.strip():
            raise HTTPException(status_code=400, detail="Search query is required.")
        return IngestionService().public_search(query, limit=limit)
    except HTTPException:
        raise
    except Exception as exc:
        raise_http(exc)


@router.post("/public-search/ingest")
def ingest_public_search(request: LiteratureIngestRequest, db: Session = Depends(get_db)):
    try:
        ingestion_service = IngestionService()
        summary = ingestion_service.ingest_public_results(db, request.results)
        return {**summary, "evidence_ids": ingestion_service.evidence_ids_for_public_results(db, request.results)}
    except Exception as exc:
        raise_http(exc)


@router.post("/public-search/ingest-and-extract")
def ingest_public_search_and_extract(request: LiteratureIngestAndExtractRequest, db: Session = Depends(get_db)):
    try:
        ingestion_service = IngestionService()
        ingestion = ingestion_service.ingest_public_results(db, request.results)
        evidence_ids = ingestion_service.evidence_ids_for_public_results(db, request.results)
        if not evidence_ids:
            return {"ingestion": ingestion, "evidence_ids": [], "application_nodes": []}
        scope = ScopeService().get_scope(db, request.scope_id)
        nodes = DescriptorExtractionService().extract_for_scope(
            db,
            scope,
            limit=max(1, min(request.limit, len(evidence_ids))),
            evidence_ids=evidence_ids,
        )
        return {"ingestion": ingestion, "evidence_ids": evidence_ids, "application_nodes": nodes}
    except Exception as exc:
        raise_http(exc)


@router.get("/status")
def ingest_status(db: Session = Depends(get_db)):
    return IngestionService().status(db)


@router.get("/descriptors")
def recent_descriptors(
    scope_id: str = "electromagnetic_functional_materials",
    limit: int = 25,
    db: Session = Depends(get_db),
):
    try:
        return IngestionService().recent_application_nodes(db, scope_id=scope_id, limit=limit)
    except Exception as exc:
        raise_http(exc)


@router.post("/extract-descriptors")
def extract_descriptors(
    request: DescriptorExtractionRequest | None = Body(default=None),
    scope_id: str = "electromagnetic_functional_materials",
    limit: int = 50,
    db: Session = Depends(get_db),
):
    try:
        scope = ScopeService().get_scope(db, scope_id)
        return DescriptorExtractionService().extract_for_scope(
            db,
            scope,
            limit=limit,
            evidence_ids=request.evidence_ids if request else None,
        )
    except Exception as exc:
        raise_http(exc)
