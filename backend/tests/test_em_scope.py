from backend.app.services.scope_service import DEFAULT_EM_SCOPE


def test_default_em_scope_contains_required_domains():
    assert DEFAULT_EM_SCOPE.scope_id == "electromagnetic_functional_materials"
    assert "metamaterials and metasurfaces" in DEFAULT_EM_SCOPE.included_domains
    assert "chalcogenides" in DEFAULT_EM_SCOPE.included_material_classes
