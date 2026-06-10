import sys
from dataclasses import replace
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.services.descriptor_extraction_service as descriptor_module
from backend.app.database import ApplicationNodeRecord, Base, EvidenceRecord
from backend.app.services.descriptor_extraction_service import DescriptorExtractionService
from backend.app.services.scope_service import DEFAULT_EM_SCOPE


def _session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return Session()


def _configure_fake_openai(monkeypatch, content: str):
    class FakeCompletions:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    fake_completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, api_key: str):
            self.api_key = api_key
            self.chat = SimpleNamespace(completions=fake_completions)

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    test_settings = replace(
        descriptor_module.settings,
        openai_api_key="test-key",
        openai_model="test-model",
        enable_openai_reasoning=True,
    )
    monkeypatch.setattr(descriptor_module, "settings", test_settings)
    return fake_completions


def _add_evidence(db, evidence_id: str, title: str, text: str, section: str = "abstract"):
    payload = {
        "evidence_id": evidence_id,
        "document_id": f"doc_{evidence_id}",
        "title": title,
        "authors": [],
        "year": 2024,
        "doi": None,
        "source_type": "openalex",
        "source_path": "https://example.test/paper",
        "page": None,
        "section": section,
        "text": text,
        "snippet": text[:420],
        "metadata": {"metadata_only": section == "metadata"},
    }
    db.add(EvidenceRecord(evidence_id=evidence_id, document_id=payload["document_id"], text=text, payload=payload))
    db.commit()


def test_descriptor_extraction_falls_back_for_in_scope_empty_model_response(monkeypatch):
    fake_completions = _configure_fake_openai(monkeypatch, '{"application_nodes":[]}')
    db = _session()
    try:
        _add_evidence(
            db,
            "ev_metadata",
            "3D metamaterials",
            "3D metamaterials\nSource: openalex\nNo abstract was available from the public metadata source.",
            section="metadata",
        )

        nodes = DescriptorExtractionService().extract_for_scope(db, DEFAULT_EM_SCOPE, limit=1)

        assert len(nodes) == 1
        assert nodes[0].label == "3D metamaterials"
        assert nodes[0].domain == "metamaterials and metasurfaces"
        assert nodes[0].evidence_ids == ["ev_metadata"]
        assert nodes[0].confidence == 0.28
        assert db.query(ApplicationNodeRecord).count() == 1
        assert fake_completions.calls[0]["response_format"] == {"type": "json_object"}
    finally:
        db.close()


def test_descriptor_fallback_prefers_specific_domain_over_generic_em_term(monkeypatch):
    _configure_fake_openai(monkeypatch, '{"application_nodes":[]}')
    db = _session()
    try:
        _add_evidence(
            db,
            "ev_inverse",
            "Deep Learning for Electromagnetic Metamaterial Inverse Design",
            "Deep Learning for Electromagnetic Metamaterial Inverse Design\nNo abstract was available from the public metadata source.",
            section="metadata",
        )

        nodes = DescriptorExtractionService().extract_for_scope(db, DEFAULT_EM_SCOPE, limit=1)

        assert len(nodes) == 1
        assert nodes[0].domain == "metamaterials and metasurfaces"
        assert nodes[0].function == "inverse design of electromagnetic response"
    finally:
        db.close()


def test_descriptor_extraction_accepts_nodes_key_and_fills_defaults(monkeypatch):
    _configure_fake_openai(
        monkeypatch,
        '{"nodes":[{"label":"Microwave absorber","application_text":"A microwave absorber controls incident electromagnetic waves.","domain":"absorbers","function":"electromagnetic absorption control","confidence":0.72}]}',
    )
    db = _session()
    try:
        _add_evidence(
            db,
            "ev_absorber",
            "Microwave metamaterial absorber",
            "Microwave metamaterial absorber with impedance matching and low loss requirements.",
        )

        nodes = DescriptorExtractionService().extract_for_scope(db, DEFAULT_EM_SCOPE, limit=1)

        assert len(nodes) == 1
        assert nodes[0].label == "Microwave absorber"
        assert nodes[0].source_ids == ["doc_ev_absorber"]
        assert nodes[0].evidence_ids == ["ev_absorber"]
        assert nodes[0].evidence_count == 1
        assert db.query(ApplicationNodeRecord).one().scope_id == DEFAULT_EM_SCOPE.scope_id
    finally:
        db.close()
