from app.core.boundaries import BOUNDARY_FLAGS, IMMUTABILITY_RULES
from app.data.phase11_2_case_baseline import PHASE11_2_CASE_BASELINE


def test_case_count_and_threshold_count():
    assert len(PHASE11_2_CASE_BASELINE) == 18
    assert sum(1 for row in PHASE11_2_CASE_BASELINE if row["ge_70"]) == 10


def test_boundary_flags_are_safe_by_default():
    assert BOUNDARY_FLAGS["not_production_ready"] is True
    assert BOUNDARY_FLAGS["not_source_backed_pass"] is True
    assert BOUNDARY_FLAGS["not_human_reviewed"] is True
    assert BOUNDARY_FLAGS["local_neural_reranker_default_enabled"] is False
    assert BOUNDARY_FLAGS["local_neural_reranker_status"] == "diagnostic_only"


def test_immutability_rules():
    assert IMMUTABILITY_RULES["must_not_rebuild_chroma"] is True
    assert IMMUTABILITY_RULES["must_not_clear_or_rebuild_neo4j"] is True
    assert IMMUTABILITY_RULES["must_not_modify_current_backend_json"] is True
