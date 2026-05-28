BOUNDARY_FLAGS = {
    "not_production_ready": True,
    "not_source_backed_pass": True,
    "not_human_reviewed": True,
    "prototype_context": True,
    "business_case_files_available": False,
    "business_evidence_files_available": False,
    "local_neural_reranker_default_enabled": False,
    "local_neural_reranker_status": "diagnostic_only",
    "bge_m3_status": "partially_effective",
    "full18_mode": "mode_a_bgem3_authority_rerank",
}

IMMUTABILITY_RULES = {
    "must_not_rebuild_chroma": True,
    "must_not_clear_or_rebuild_neo4j": True,
    "must_not_modify_current_backend_json": True,
    "must_not_fabricate_source_backed": True,
    "must_not_fabricate_manual_verified": True,
    "must_not_fabricate_article_level_verified": True,
    "must_not_enable_local_neural_reranker_by_default": True,
}
