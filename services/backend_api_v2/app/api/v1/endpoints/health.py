from fastapi import APIRouter

from app.core.boundaries import BOUNDARY_FLAGS, IMMUTABILITY_RULES
from app.core.config import get_settings
from app.core.project_paths import get_project_paths
from app.services.llm_config_service import LLMConfigService
from app.services.multi_agent_runtime_adapter import MultiAgentRuntimeAdapter
try:
    from core.evaluation.autojudge_runner import agent_llm_config_summary
except ModuleNotFoundError:
    def agent_llm_config_summary() -> dict:
        return {"agent_llm_api_key_present": False}

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    paths = get_project_paths()
    adapter = MultiAgentRuntimeAdapter()
    llm_summary = LLMConfigService().summary()
    return {
        "ok": True,
        "service": "reguthink-backend-api-v2",
        "phase": settings.phase,
        "project_root": str(paths.project_root),
        "project_root_exists": paths.project_root.exists(),
        "full18_run_root": str(paths.full18_run_root),
        "full18_run_root_exists": paths.full18_run_root.exists(),
        "runtime_enabled": settings.enable_runtime,
        "runtime_mode": settings.runtime_mode,
        "interactive_backend_enabled": settings.interactive_backend_enabled,
        "runtime_storage_root": str(paths.runtime_storage_root),
        "conversation_api_enabled": settings.conversation_api_enabled,
        "file_upload_enabled": settings.file_upload_enabled,
        "sse_stream_enabled": settings.sse_stream_enabled,
        "assessment_types_enabled": settings.assessment_types_enabled,
        "dry_run_assessment_available": settings.dry_run_assessment_available,
        "controlled_runtime_available": settings.controlled_runtime_available,
        "real_multi_agent_runtime_enabled": settings.real_multi_agent_runtime_enabled,
        "real_multi_agent_runtime_adapter_status": adapter.adapter_status(),
        "runtime_capabilities": adapter.get_runtime_capabilities(),
        "uploaded_material_runtime_supported": True,
        "full_chain_runtime_supported": True,
        "controlled_case_runtime_supported": True,
        "real_autojudge_available": agent_llm_config_summary().get("agent_llm_api_key_present", False),
        "autojudge_runtime_integrated": True,
        "llm_config_available": llm_summary["llm_config_available"],
        "llm_provider_configured": llm_summary["llm_provider_configured"],
        "llm_key_present": llm_summary["key_present"],
        "llm_model_family": llm_summary["model_family"],
        "llm_model_name_masked": llm_summary["model_name_masked"],
        "local_neural_reranker_default_enabled": BOUNDARY_FLAGS["local_neural_reranker_default_enabled"],
        "boundary_flags": BOUNDARY_FLAGS,
        "immutability_rules": IMMUTABILITY_RULES,
    }
