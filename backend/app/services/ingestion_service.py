from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from ..config import settings
from ..database import ApplicationNodeRecord, DocumentRecord, EvidenceRecord
from ..ingestion.chunker import chunk_pages
from ..ingestion.deduplicator import document_key, file_hash
from ..ingestion.metadata_extractor import extract_metadata, normalize_doi
from ..ingestion.pdf_parser import parse_pdf
from ..ingestion.text_parser import parse_text_file
from ..literature_sources.arxiv_source import ArxivSource
from ..literature_sources.base import LiteratureSearchResult
from ..literature_sources.crossref import CrossrefSource
from ..literature_sources.openalex import OpenAlexSource
from ..literature_sources.pubmed import PubMedSource
from ..literature_sources.zotero_import import import_zotero_file
from ..schemas import Document, EvidenceChunk, LiteratureResult
from .ids import stable_id
from .object_storage_service import ObjectStorageService
from .serialization import model_to_dict


class IngestionService:
    supported_text_suffixes = {".txt", ".md", ".markdown"}

    def ingest_local(self, db: Session) -> Dict[str, int]:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        counts = {"documents": 0, "chunks": 0, "skipped": 0}
        object_storage = ObjectStorageService()
        paths: List[Path] = []
        paths.extend(sorted((settings.data_dir / "pdfs").glob("*.pdf")))
        evidence_dir = settings.data_dir / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        for suffix in self.supported_text_suffixes:
            paths.extend(sorted(evidence_dir.glob(f"*{suffix}")))

        for path in paths:
            parsed = self._parse_path(path)
            if not parsed:
                counts["skipped"] += 1
                continue
            first_text = "\n".join(text for _, _, text in parsed[:3])
            meta = extract_metadata(path, first_text)
            doi = normalize_doi(meta.get("doi")) if isinstance(meta.get("doi"), str) else None
            doc_key = document_key(doi, str(meta["title"]), path)
            document_id = stable_id("doc", doc_key)
            if db.get(DocumentRecord, document_id):
                counts["skipped"] += 1
                continue
            source_path = str(path)
            object_path = self._storage_object_for_local_path(path)
            if object_path:
                source_path = object_storage.upload_file(path, object_path)
            document = Document(
                document_id=document_id,
                title=str(meta["title"]),
                authors=list(meta.get("authors") or []),
                year=meta.get("year") if isinstance(meta.get("year"), int) else None,
                doi=doi,
                source_type="local_pdf" if path.suffix.lower() == ".pdf" else "local_text",
                source_path=source_path,
                metadata={"file_hash": file_hash(path), "original_name": path.name},
            )
            db.add(DocumentRecord(document_id=document_id, doi=doi, title=document.title, payload=model_to_dict(document)))
            chunk_rows = []
            for idx, (page, section, text) in enumerate(chunk_pages(parsed), start=1):
                evidence_id = stable_id("ev", document_id, page, section, idx, text[:120])
                chunk = EvidenceChunk(
                    evidence_id=evidence_id,
                    document_id=document_id,
                    title=document.title,
                    authors=document.authors,
                    year=document.year,
                    doi=document.doi,
                    source_type=document.source_type,
                    source_path=document.source_path,
                    page=page,
                    section=section,
                    text=text,
                    snippet=text[:420],
                    metadata={"chunk_index": idx},
                )
                chunk_rows.append(EvidenceRecord(evidence_id=evidence_id, document_id=document_id, text=text, payload=model_to_dict(chunk)))
            db.add_all(chunk_rows)
            counts["documents"] += 1
            counts["chunks"] += len(chunk_rows)
        db.commit()
        self._write_jsonl_backup(db)
        return counts

    def ingest_zotero(self, db: Session) -> Dict[str, int]:
        zotero_dir = settings.data_dir / "zotero"
        zotero_dir.mkdir(parents=True, exist_ok=True)
        added = 0
        for export_path in sorted(list(zotero_dir.glob("*.csv")) + list(zotero_dir.glob("*.bib")) + list(zotero_dir.glob("*.ris"))):
            for result in import_zotero_file(export_path):
                if self._store_metadata_result(db, result):
                    added += 1
        db.commit()
        return {"metadata_records": added}

    def public_search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        if not settings.enable_online_metadata:
            return []
        query = query.strip()
        if not query:
            return []
        requested_limit = max(1, min(int(limit or 10), 200))
        sources = [
            OpenAlexSource(settings.literature_contact_email),
            CrossrefSource(settings.literature_contact_email),
            ArxivSource(),
            PubMedSource(settings.literature_contact_email),
        ]
        results: List[LiteratureSearchResult] = []
        per_source_limit = max(1, min(75, (requested_limit + len(sources) - 1) // len(sources)))
        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            future_by_source = {executor.submit(source.search, query, per_source_limit): source for source in sources}
            for future in as_completed(future_by_source):
                try:
                    results.extend(future.result())
                except Exception:
                    continue
        return self._dedupe_results(results)[:requested_limit]

    def ingest_public_results(self, db: Session, results: List[LiteratureResult]) -> Dict[str, int]:
        before_documents = db.query(DocumentRecord).count()
        before_evidence = db.query(EvidenceRecord).count()
        skipped = 0
        for result in results:
            title = result.title.strip()
            if not title or title.endswith(" search failed"):
                skipped += 1
                continue
            source_result = LiteratureSearchResult(
                title=title,
                authors=result.authors,
                year=result.year,
                doi=result.doi,
                url=result.url,
                source=result.source,
                abstract=result.abstract,
                extra=result.extra or {},
            )
            if not self._store_metadata_result(db, source_result):
                skipped += 1
        db.commit()
        self._write_jsonl_backup(db)
        after_documents = db.query(DocumentRecord).count()
        after_evidence = db.query(EvidenceRecord).count()
        return {
            "documents_added": after_documents - before_documents,
            "evidence_chunks_added": after_evidence - before_evidence,
            "skipped": skipped,
            "documents": after_documents,
            "evidence_chunks": after_evidence,
        }

    def evidence_ids_for_public_results(self, db: Session, results: List[LiteratureResult]) -> List[str]:
        evidence_ids: List[str] = []
        for result in results:
            title = result.title.strip()
            if not title or title.endswith(" search failed"):
                continue
            doi = normalize_doi(result.doi)
            existing = db.query(DocumentRecord).filter(DocumentRecord.doi == doi).first() if doi else None
            document_id = existing.document_id if existing else stable_id("doc", doi or title, result.year or "")
            section = "abstract" if (result.abstract or "").strip() else "metadata"
            evidence_id = stable_id("ev", document_id, section)
            if db.get(EvidenceRecord, evidence_id):
                evidence_ids.append(evidence_id)
        return evidence_ids

    def status(self, db: Session) -> Dict[str, int]:
        return {
            "documents": db.query(DocumentRecord).count(),
            "evidence_chunks": db.query(EvidenceRecord).count(),
            "application_nodes": db.query(ApplicationNodeRecord).count(),
        }

    def _parse_path(self, path: Path) -> List[tuple]:
        if path.suffix.lower() == ".pdf":
            return parse_pdf(path)
        if path.suffix.lower() in self.supported_text_suffixes:
            return parse_text_file(path)
        return []

    def _store_metadata_result(self, db: Session, result: LiteratureSearchResult) -> bool:
        doi = normalize_doi(result.doi)
        document_id = stable_id("doc", doi or result.title, result.year or "")
        existing = db.query(DocumentRecord).filter(DocumentRecord.doi == doi).first() if doi else None
        if not existing:
            existing = db.get(DocumentRecord, document_id)

        added = False
        if existing:
            document = Document(**existing.payload)
        else:
            document = Document(
                document_id=document_id,
                title=result.title,
                authors=result.authors,
                year=result.year,
                doi=doi,
                source_type=result.source,
                source_path=result.url,
                metadata=result.extra or {},
            )
            db.add(DocumentRecord(document_id=document_id, doi=doi, title=document.title, payload=model_to_dict(document)))
            added = True

        if self._store_metadata_evidence(db, document, result):
            added = True
        db.flush()
        return added

    def _store_metadata_evidence(self, db: Session, document: Document, result: LiteratureSearchResult) -> bool:
        text, section = self._metadata_evidence_text(result)
        evidence_id = stable_id("ev", document.document_id, section)
        if db.get(EvidenceRecord, evidence_id):
            return False
        chunk = EvidenceChunk(
            evidence_id=evidence_id,
            document_id=document.document_id,
            title=document.title,
            authors=document.authors,
            year=document.year,
            doi=document.doi,
            source_type=result.source,
            source_path=result.url,
            page=None,
            section=section,
            text=text,
            snippet=text[:420],
            metadata={"source": result.source, "metadata_only": section == "metadata"},
        )
        db.add(EvidenceRecord(evidence_id=evidence_id, document_id=document.document_id, text=chunk.text, payload=model_to_dict(chunk)))
        return True

    def _metadata_evidence_text(self, result: LiteratureSearchResult) -> tuple[str, str]:
        abstract = (result.abstract or "").strip()
        if abstract:
            return abstract, "abstract"
        lines = [
            result.title.strip(),
            f"Authors: {', '.join(result.authors)}" if result.authors else "",
            f"Year: {result.year}" if result.year else "",
            f"DOI: {normalize_doi(result.doi)}" if result.doi else "",
            f"URL: {result.url}" if result.url else "",
            f"Source: {result.source}",
            "No abstract was available from the public metadata source.",
        ]
        return "\n".join(line for line in lines if line), "metadata"

    def _dedupe_results(self, results: List[LiteratureSearchResult]) -> List[LiteratureSearchResult]:
        seen = set()
        deduped = []
        for result in results:
            key = normalize_doi(result.doi) or " ".join(result.title.lower().split())
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(result)
        return deduped

    def _write_jsonl_backup(self, db: Session) -> None:
        backup_path = settings.data_dir / "metadata" / "evidence_chunks.jsonl"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        with backup_path.open("w", encoding="utf-8") as handle:
            for record in db.query(EvidenceRecord).order_by(EvidenceRecord.evidence_id):
                handle.write(json.dumps(record.payload, ensure_ascii=True) + "\n")
        ObjectStorageService().upload_file(
            backup_path,
            "metadata/evidence_chunks.jsonl",
            content_type="application/x-ndjson",
        )

    def _storage_object_for_local_path(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return f"uploads/pdfs/{path.name}"
        if suffix in self.supported_text_suffixes:
            return f"uploads/evidence/{path.name}"
        return ""
