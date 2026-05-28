from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.core.project_paths import get_project_paths
from app.data.phase11_2_case_baseline import CASE_IDS


class RuntimeAdapter:
    """Controlled adapter for future single-case runtime.

    This class intentionally defaults to dry-run behavior. It must not trigger full18,
    rebuild Chroma, clear Neo4j, modify current_backend.json, or enable local neural reranker.
    """

    def run_case(self, case_id: str, dry_run: bool = True, runtime_profile: Optional[str] = None) -> Dict[str, Any]:
        settings = get_settings()
        paths = get_project_paths()
        if case_id not in CASE_IDS:
            return {
                "ok": False,
                "case_id": case_id,
                "message": "Unknown case_id.",
                "allowed_case_ids": CASE_IDS,
            }

        planned = {
            "case_id": case_id,
            "runtime_profile": runtime_profile or "single_case_diagnostic_mode_a_bgem3_authority_rerank",
            "project_root": str(paths.project_root),
            "full18_baseline_root": str(paths.full18_run_root),
            "will_modify_current_backend_json": False,
            "will_rebuild_chroma": False,
            "will_clear_or_rebuild_neo4j": False,
            "will_enable_local_neural_reranker": False,
            "will_claim_production_ready": False,
            "will_claim_source_backed_pass": False,
            "dry_run": dry_run,
        }

        if dry_run:
            return {
                "ok": True,
                "mode": "dry_run",
                "message": "Runtime is planned but not executed. This is the safe default.",
                "planned_execution": planned,
            }

        if not settings.enable_runtime:
            return {
                "ok": False,
                "mode": "runtime_disabled",
                "message": "Set REGUTHINK_API_ENABLE_RUNTIME=1 only after read-only API smoke tests pass.",
                "planned_execution": planned,
            }

        # Runtime integration should be wired here after verifying the exact local
        # core/v12 function/CLI contract in the real repository. We do not guess it.
        return {
            "ok": False,
            "mode": "not_implemented_safe_fail",
            "message": "Runtime execution is intentionally not implemented in this greenfield shell until the exact core/v12 runner contract is verified locally.",
            "planned_execution": planned,
        }
