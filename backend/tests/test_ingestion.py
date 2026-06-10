from dataclasses import replace
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.services.ingestion_service as ingestion_module
import backend.app.services.object_storage_service as storage_module
from backend.app.config import settings as app_settings
from backend.app.database import Base, DocumentRecord, EvidenceRecord
from backend.app.ingestion.chunker import chunk_text
from backend.app.ingestion.metadata_extractor import extract_metadata
from backend.app.schemas import LiteratureResult
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.object_storage_service import ObjectStorageService


def test_text_chunking_preserves_nonempty_chunks():
    chunks = chunk_text("Sentence one. " * 400, max_chars=500)
    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)


def test_metadata_extractor_finds_doi_and_year(tmp_path: Path):
    path = tmp_path / "paper.txt"
    text = "Electromagnetic material paper\nDOI 10.1016/j.example.2024.1 published in 2024"
    metadata = extract_metadata(path, text)
    assert metadata["doi"] == "10.1016/j.example.2024.1"
    assert metadata["year"] == 2024


def test_object_storage_service_local_mode_returns_local_path(tmp_path: Path):
    path = tmp_path / "artifact.json"
    path.write_text("{}", encoding="utf-8")
    assert ObjectStorageService().upload_file(path) == str(path)


def test_public_literature_results_ingest_and_skip_duplicates(tmp_path: Path, monkeypatch):
    test_settings = replace(app_settings, data_dir=tmp_path, object_storage_backend="local")
    monkeypatch.setattr(ingestion_module, "settings", test_settings)
    monkeypatch.setattr(storage_module, "settings", test_settings)

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = Session()
    try:
        summary = IngestionService().ingest_public_results(
            db,
            [
                LiteratureResult(
                    title="Inverse Design of Electromagnetic Metamaterials",
                    authors=["A. Researcher"],
                    year=2025,
                    doi="10.1000/example",
                    url="https://example.test/paper",
                    source="openalex",
                    abstract="High permittivity, low loss electromagnetic metamaterial design evidence.",
                ),
                LiteratureResult(
                    title="Duplicate DOI",
                    authors=[],
                    doi="10.1000/example",
                    source="crossref",
                    abstract="Duplicate metadata should be skipped.",
                ),
                LiteratureResult(title="openalex search failed", source="openalex"),
            ],
        )

        assert summary["documents_added"] == 1
        assert summary["evidence_chunks_added"] == 1
        assert summary["skipped"] == 2
        assert db.query(DocumentRecord).count() == 1
        assert db.query(EvidenceRecord).one().text.startswith("High permittivity")
        assert (tmp_path / "metadata" / "evidence_chunks.jsonl").exists()
    finally:
        db.close()
