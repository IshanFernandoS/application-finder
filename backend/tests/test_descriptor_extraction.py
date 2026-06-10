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


def test_descriptor_extraction_can_filter_to_selected_evidence(monkeypatch):
    fake_completions = _configure_fake_openai(monkeypatch, '{"application_nodes":[]}')
    db = _session()
    try:
        _add_evidence(
            db,
            "ev_selected",
            "Selected Electromagnetic Metamaterial Paper",
            "Selected electromagnetic metamaterial evidence.",
            section="metadata",
        )
        _add_evidence(
            db,
            "ev_other",
            "Other Electromagnetic Absorber Paper",
            "Other electromagnetic absorber evidence that should not be extracted.",
            section="metadata",
        )

        nodes = DescriptorExtractionService().extract_for_scope(db, DEFAULT_EM_SCOPE, limit=10, evidence_ids=["ev_selected"])

        assert len(nodes) == 1
        assert nodes[0].evidence_ids == ["ev_selected"]
        assert len(fake_completions.calls) == 1
    finally:
        db.close()


def test_descriptor_extraction_merges_duplicate_node_ids_in_one_run(monkeypatch):
    _configure_fake_openai(
        monkeypatch,
        '{"application_nodes":[{"node_id":"node_duplicate","label":"Shared descriptor","application_text":"Shared electromagnetic metamaterial descriptor.","domain":"metamaterials and metasurfaces","function":"electromagnetic response engineering","confidence":0.5}]}',
    )
    db = _session()
    try:
        _add_evidence(
            db,
            "ev_first",
            "First Electromagnetic Metamaterial Paper",
            "First electromagnetic metamaterial evidence.",
            section="metadata",
        )
        _add_evidence(
            db,
            "ev_second",
            "Second Electromagnetic Metamaterial Paper",
            "Second electromagnetic metamaterial evidence.",
            section="metadata",
        )

        nodes = DescriptorExtractionService().extract_for_scope(db, DEFAULT_EM_SCOPE, limit=2)

        assert len(nodes) == 2
        assert db.query(ApplicationNodeRecord).count() == 1
        record = db.get(ApplicationNodeRecord, "node_duplicate")
        assert record is not None
        assert record.payload["node_id"] == "node_duplicate"
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


def test_descriptor_extraction_normalizes_scalar_list_fields(monkeypatch):
    _configure_fake_openai(
        monkeypatch,
        (
            '{"application_nodes":[{'
            '"label":"X-ray stable electromagnetic absorber",'
            '"application_text":"A stable electromagnetic absorber descriptor.",'
            '"domain":"absorbers",'
            '"function":"electromagnetic absorption control",'
            '"material_names":null,'
            '"em_property_requirements":"distinct and measurable permittivity under X-ray exposure",'
            '"non_em_constraints":"algorithmic stability for inverse design; computational efficiency",'
            '"confidence":0.67'
            "}]}"
        ),
    )
    db = _session()
    try:
        _add_evidence(
            db,
            "ev_scalar_lists",
            "X-ray stable electromagnetic absorber",
            "An electromagnetic absorber descriptor with measurable permittivity and validation constraints.",
        )

        nodes = DescriptorExtractionService().extract_for_scope(db, DEFAULT_EM_SCOPE, limit=1)

        assert len(nodes) == 1
        assert nodes[0].material_names == []
        assert nodes[0].em_property_requirements == ["distinct and measurable permittivity under X-ray exposure"]
        assert nodes[0].non_em_constraints == ["algorithmic stability for inverse design", "computational efficiency"]
        assert db.query(ApplicationNodeRecord).count() == 1
    finally:
        db.close()


def test_descriptor_extraction_normalizes_qualitative_confidence(monkeypatch):
    _configure_fake_openai(
        monkeypatch,
        (
            '{"application_nodes":[{'
            '"label":"Low confidence absorber descriptor",'
            '"application_text":"A title-derived electromagnetic absorber descriptor.",'
            '"domain":"absorbers",'
            '"function":"electromagnetic absorption control",'
            '"confidence":"low"'
            "}]}"
        ),
    )
    db = _session()
    try:
        _add_evidence(
            db,
            "ev_low_confidence",
            "Low Confidence Electromagnetic Absorber",
            "Electromagnetic absorber metadata with limited descriptor evidence.",
            section="metadata",
        )

        nodes = DescriptorExtractionService().extract_for_scope(db, DEFAULT_EM_SCOPE, limit=1)

        assert len(nodes) == 1
        assert nodes[0].confidence == 0.28
        assert db.query(ApplicationNodeRecord).count() == 1
    finally:
        db.close()
