from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
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
def public_search(query: str, limit: int = 10):
    try:
        return IngestionService().public_search(query, limit=limit)
    except Exception as exc:
        raise_http(exc)


@router.get("/status")
def ingest_status(db: Session = Depends(get_db)):
    return IngestionService().status(db)


@router.post("/extract-descriptors")
def extract_descriptors(scope_id: str = "electromagnetic_functional_materials", limit: int = 50, db: Session = Depends(get_db)):
    try:
        scope = ScopeService().get_scope(db, scope_id)
        return DescriptorExtractionService().extract_for_scope(db, scope, limit=limit)
    except Exception as exc:
        raise_http(exc)
