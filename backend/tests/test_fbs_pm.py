from backend.app.reasoning.evidence_validator import validate_fbs_pm_chain
from backend.app.schemas import EvidenceSupport, FBSPMPathway, MaterialCandidate, PropertyRequirement


def test_evidence_validator_flags_direct_material_jump():
    pathway = FBSPMPathway(
        pathway_id="p1",
        gap_id="g1",
        title="Invalid direct jump",
        pathway_type=EvidenceSupport.speculative,
        summary="fixture",
        pseudo_application="application",
        function="function",
        behaviour_or_mechanism="mechanism",
        structure_or_device_realization="device",
        material_property_envelope=[],
        candidate_materials=[
            MaterialCandidate(candidate_id="c1", material="TiO2", material_class="oxide", role_in_device="coating")
        ],
        uncertainty="missing property envelope",
    )
    result = validate_fbs_pm_chain(pathway, [])
    assert result["direct_application_to_material_jump"] is True
    assert result["valid"] is False
