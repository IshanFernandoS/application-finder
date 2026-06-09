from backend.app.evaluation.descriptor_eval import descriptor_metrics
from backend.app.schemas import ApplicationNode


def test_descriptor_metrics_run_on_fixture_nodes():
    metrics = descriptor_metrics(
        [
            ApplicationNode(
                node_id="n1",
                label="IR coating",
                application_text="IR thermal emissivity coating",
                domain="infrared and thermal-emissivity devices",
                function="control emissivity",
                device_type="photonic coating",
                physical_em_mechanism="photonic interference",
                material_class="oxide",
                em_property_requirements=["emissivity"],
                evidence_ids=["ev1"],
                confidence=0.9,
            )
        ]
    )
    assert metrics["field_completion_rate"] > 0.5
