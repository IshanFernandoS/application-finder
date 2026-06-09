from backend.app.reasoning.constraint_translator import translate_constraints
from backend.app.schemas import EvidenceSupport, FBSPMPathway, PropertyRequirement


def test_constraint_translator_retains_unsupported_em_properties():
    pathway = FBSPMPathway(
        pathway_id="p1",
        gap_id="g1",
        title="THz absorber route",
        pathway_type=EvidenceSupport.analogy_supported,
        summary="fixture",
        pseudo_application="THz absorber",
        function="absorb THz radiation",
        behaviour_or_mechanism="impedance matching",
        structure_or_device_realization="metasurface coating",
        material_property_envelope=[
            PropertyRequirement(
                property_name="loss tangent",
                property_category="dielectric",
                desired_direction="specific_range",
                target_range_or_qualitative_requirement="high enough for absorption",
                why_required="Controls absorption bandwidth.",
            )
        ],
        uncertainty="fixture",
    )
    constraints = translate_constraints(pathway)
    assert constraints.unsupported_em_properties
