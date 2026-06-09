from backend.app.application_space.gap_characterization import pseudo_application_from_boundary, summarize_boundary
from backend.app.schemas import ApplicationNode


def test_boundary_summary_uses_em_descriptors():
    nodes = [
        ApplicationNode(
            node_id="n1",
            label="RF sensor",
            application_text="RF sensor",
            domain="RF/microwave sensing",
            function="sense strain",
            device_type="sensor",
            physical_em_mechanism="dielectric shift",
            material_class="oxide",
            em_property_requirements=["permittivity"],
            confidence=0.8,
        )
    ]
    boundary = summarize_boundary(nodes)
    assert boundary["domains"] == ["RF/microwave sensing"]
    assert pseudo_application_from_boundary(boundary)
