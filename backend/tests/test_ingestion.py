from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.services.ingestion_service as ingestion_module
import backend.app.services.object_storage_service as storage_module
from backend.app.config import settings as app_settings
from backend.app.database import ApplicationNodeRecord, Base, DocumentRecord, EvidenceRecord
from backend.app.ingestion.chunker import chunk_text
from backend.app.ingestion.metadata_extractor import extract_metadata
from backend.app.literature_sources.base import LiteratureSearchResult
from backend.app.schemas import LiteratureResult
from backend.app.services.full_text_retrieval_service import RetrievedFullText
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.object_storage_service import ObjectStorageService


class NoFullTextService:
    def has_retrieval_lead(self, result):
        return False

    def retrieve(self, result, document_id):
        return None


@pytest.fixture(autouse=True)
def disable_public_full_text_network(monkeypatch):
    monkeypatch.setattr(ingestion_module, "FullTextRetrievalService", NoFullTextService)


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


def test_object_storage_service_local_mode_returns_local_path(tmp_path: Path, monkeypatch):
    test_settings = replace(app_settings, object_storage_backend="local")
    monkeypatch.setattr(storage_module, "settings", test_settings)
    path = tmp_path / "artifact.json"
    path.write_text("{}", encoding="utf-8")
    assert ObjectStorageService().upload_file(path) == str(path)


def test_public_search_uses_curated_sources_and_larger_limit(monkeypatch):
    _configure_fake_literature_sources(monkeypatch)

    results = IngestionService().public_search("electromagnetic absorber", limit=120)

    assert len(results) == 120
    assert {result.source for result in results} == {"arxiv", "crossref", "openalex", "pubmed"}
    assert "semantic_scholar" not in {result.source for result in results}


def test_public_search_skips_source_failures(monkeypatch):
    _configure_fake_literature_sources(monkeypatch, failing_source="crossref")

    results = IngestionService().public_search("electromagnetic absorber", limit=20)

    assert len(results) == 15
    assert {result.source for result in results} == {"arxiv", "openalex", "pubmed"}
    assert not any(result.title.endswith("search failed") for result in results)


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
        assert IngestionService().evidence_ids_for_public_results(
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
                )
            ],
        )
        assert (tmp_path / "metadata" / "evidence_chunks.jsonl").exists()
    finally:
        db.close()


def _configure_fake_literature_sources(monkeypatch, failing_source: str | None = None):
    test_settings = replace(app_settings, enable_online_metadata=True)
    monkeypatch.setattr(ingestion_module, "settings", test_settings)

    def source_factory(source_name: str):
        class FakeSource:
            def __init__(self, *args, **kwargs):
                self.source_name = source_name

            def search(self, query: str, limit: int = 10):
                if source_name == failing_source:
                    raise RuntimeError("provider unavailable")
                return [
                    LiteratureSearchResult(
                        title=f"{source_name} paper {index} {query}",
                        authors=["A. Researcher"],
                        year=2024,
                        doi=f"10.1000/{source_name}.{index}",
                        url=f"https://example.test/{source_name}/{index}",
                        source=source_name,
                        abstract="Electromagnetic material evidence.",
                    )
                    for index in range(limit)
                ]

        return FakeSource

    monkeypatch.setattr(ingestion_module, "OpenAlexSource", source_factory("openalex"))
    monkeypatch.setattr(ingestion_module, "CrossrefSource", source_factory("crossref"))
    monkeypatch.setattr(ingestion_module, "ArxivSource", source_factory("arxiv"))
    monkeypatch.setattr(ingestion_module, "PubMedSource", source_factory("pubmed"))


def test_public_literature_ingest_creates_metadata_evidence_without_abstract(tmp_path: Path, monkeypatch):
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
                    title="Metadata Only Electromagnetic Materials Paper",
                    authors=["A. Researcher", "B. Scientist"],
                    year=2024,
                    doi="10.1000/noabstract",
                    url="https://example.test/no-abstract",
                    source="openalex",
                    extra=None,
                )
            ],
        )

        assert summary["documents_added"] == 1
        assert summary["evidence_chunks_added"] == 1
        chunk = db.query(EvidenceRecord).one()
        assert chunk.payload["section"] == "metadata"
        assert chunk.payload["metadata"]["metadata_only"] is True
        assert "No abstract was available" in chunk.text
        assert "Metadata Only Electromagnetic Materials Paper" in chunk.text
        assert IngestionService().evidence_ids_for_public_results(
            db,
            [
                LiteratureResult(
                    title="Metadata Only Electromagnetic Materials Paper",
                    authors=["A. Researcher", "B. Scientist"],
                    year=2024,
                    doi="10.1000/noabstract",
                    url="https://example.test/no-abstract",
                    source="openalex",
                    extra=None,
                )
            ],
        ) == [chunk.evidence_id]
    finally:
        db.close()


def test_public_literature_ingest_backfills_missing_metadata_evidence(tmp_path: Path, monkeypatch):
    test_settings = replace(app_settings, data_dir=tmp_path, object_storage_backend="local")
    monkeypatch.setattr(ingestion_module, "settings", test_settings)
    monkeypatch.setattr(storage_module, "settings", test_settings)

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = Session()
    try:
        document = {
            "document_id": "doc_existing",
            "title": "Existing Metadata Only Paper",
            "authors": [],
            "year": 2024,
            "doi": "10.1000/existing",
            "source_type": "openalex",
            "source_path": "https://example.test/existing",
            "metadata": {},
        }
        db.add(DocumentRecord(document_id=document["document_id"], doi=document["doi"], title=document["title"], payload=document))
        db.commit()

        summary = IngestionService().ingest_public_results(
            db,
            [
                LiteratureResult(
                    title="Existing Metadata Only Paper",
                    year=2024,
                    doi="10.1000/existing",
                    url="https://example.test/existing",
                    source="openalex",
                )
            ],
        )

        assert summary["documents_added"] == 0
        assert summary["evidence_chunks_added"] == 1
        assert summary["skipped"] == 0
        assert db.query(DocumentRecord).count() == 1
        assert db.query(EvidenceRecord).one().payload["section"] == "metadata"
    finally:
        db.close()


def test_public_literature_ingest_stores_open_full_text_chunks(tmp_path: Path, monkeypatch):
    test_settings = replace(
        app_settings,
        data_dir=tmp_path,
        object_storage_backend="local",
        public_full_text_max_chunks_per_paper=4,
        public_full_text_descriptor_chunks_per_paper=2,
    )
    monkeypatch.setattr(ingestion_module, "settings", test_settings)
    monkeypatch.setattr(storage_module, "settings", test_settings)

    class FakeFullTextService:
        def has_retrieval_lead(self, result):
            return True

        def retrieve(self, result, document_id):
            return RetrievedFullText(
                source_url="https://open.example.test/paper.pdf",
                content_type="application/pdf",
                pages=[
                    (1, "page", "Introduction text without much electromagnetic detail."),
                    (
                        2,
                        "page",
                        "Metasurface absorber evidence with high permittivity, low loss tangent, "
                        "impedance matching, microwave GHz response, dielectric material constraints. " * 8,
                    ),
                    (
                        3,
                        "page",
                        "Fabrication and experiment evidence for dielectric metamaterial absorption. " * 8,
                    ),
                ],
                metadata={"retrieval_method": "test_open_access"},
            )

    monkeypatch.setattr(ingestion_module, "FullTextRetrievalService", FakeFullTextService)

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = Session()
    try:
        result = LiteratureResult(
            title="Open Full Text Electromagnetic Metasurface Absorber",
            authors=["A. Researcher"],
            year=2025,
            doi="10.1000/open-full-text",
            url="https://example.test/open",
            source="openalex",
            abstract="Abstract fallback should not be the preferred descriptor evidence.",
            extra={"pdf_url": "https://open.example.test/paper.pdf"},
        )
        summary = IngestionService().ingest_public_results(db, [result])

        assert summary["documents_added"] == 1
        assert summary["evidence_chunks_added"] == 4
        chunks = db.query(EvidenceRecord).all()
        full_text_chunks = [chunk for chunk in chunks if chunk.payload["metadata"].get("public_full_text")]
        assert len(full_text_chunks) == 3
        assert {chunk.payload["source_type"] for chunk in full_text_chunks} == {"public_full_text_pdf"}
        evidence_ids = IngestionService().evidence_ids_for_public_results(db, [result])
        assert len(evidence_ids) == 2
        selected_text = "\n".join(db.get(EvidenceRecord, evidence_id).text for evidence_id in evidence_ids)
        assert "permittivity" in selected_text
        assert "loss tangent" in selected_text
    finally:
        db.close()


def test_recent_application_nodes_returns_saved_descriptors(tmp_path: Path, monkeypatch):
    test_settings = replace(app_settings, data_dir=tmp_path, object_storage_backend="local")
    monkeypatch.setattr(ingestion_module, "settings", test_settings)
    monkeypatch.setattr(storage_module, "settings", test_settings)

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = Session()
    try:
        db.add_all(
            [
                ApplicationNodeRecord(
                    node_id="node_a",
                    scope_id="electromagnetic_functional_materials",
                    payload={"node_id": "node_a", "label": "First descriptor"},
                ),
                ApplicationNodeRecord(
                    node_id="node_b",
                    scope_id="electromagnetic_functional_materials",
                    payload={"node_id": "node_b", "label": "Second descriptor"},
                ),
                ApplicationNodeRecord(
                    node_id="node_other_scope",
                    scope_id="other_scope",
                    payload={"node_id": "node_other_scope", "label": "Other scope"},
                ),
            ]
        )
        db.commit()

        nodes = IngestionService().recent_application_nodes(db, "electromagnetic_functional_materials", limit=10)

        assert [node["node_id"] for node in nodes] == ["node_b", "node_a"]
    finally:
        db.close()
