from pathlib import Path

from backend.app.ingestion.chunker import chunk_text
from backend.app.ingestion.metadata_extractor import extract_metadata
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
