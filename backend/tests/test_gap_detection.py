from backend.app.schemas import Gap


def test_gap_schema_requires_application_space_chain_fields():
    gap = Gap(
        gap_id="gap_fixture",
        scope_id="electromagnetic_functional_materials",
        title="Boundary gap",
        coordinates=[0.0, 1.0],
        nearby_cluster_ids=["cluster_1"],
        nearby_application_ids=["node_1"],
        missing_descriptor_combination={"domain": "THz sensing"},
        boundary_descriptors={"mechanisms": ["phase transition"]},
        pseudo_application_hypotheses=["THz sensing through phase transition"],
        novelty_score=0.7,
        feasibility_score=0.6,
        boundary_evidence_score=0.5,
        neighbour_diversity_score=0.8,
        mattergen_compatibility_score=0.4,
        uncertainty_score=0.3,
        overall_gap_score=0.62,
        explanation="Fixture gap.",
    )
    assert gap.pseudo_application_hypotheses[0].startswith("THz")
