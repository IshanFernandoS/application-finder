from backend.app.schemas import ApplicationNode, PropertyRequirement, ValidationStatus


def test_application_node_schema_validates():
    node = ApplicationNode(
        node_id="node_fixture",
        label="THz tunable absorber",
        application_text="A tunable THz absorber using phase-change materials.",
        domain="metamaterials and metasurfaces",
        function="absorb incident THz radiation",
        physical_em_mechanism="phase transition",
        material_class="chalcogenide",
        evidence_ids=["ev_1"],
        confidence=0.82,
    )
    assert node.domain.startswith("metamaterials")
    assert node.evidence_ids == ["ev_1"]


def test_property_requirement_keeps_mattergen_support_flag():
    req = PropertyRequirement(
        property_name="complex permittivity",
        property_category="dielectric",
        desired_direction="tunable",
        target_range_or_qualitative_requirement="frequency-dependent tunability at THz",
        why_required="Controls absorber impedance matching.",
    )
    assert req.mattergen_direct_support == "unsupported"


def test_validation_statuses_include_em_simulation():
    assert ValidationStatus.em_simulation_pending.value == "EM-simulation-pending"
