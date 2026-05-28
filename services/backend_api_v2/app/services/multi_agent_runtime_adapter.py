from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from app.core.boundaries import BOUNDARY_FLAGS
from app.core.config import get_settings
from app.models.job import RuntimeMode
from app.services.runtime_storage import RuntimeStorage
from app.services.storage_utils import write_json_atomic


class MultiAgentRuntimeAdapter:
    """Controlled BE3 adapter for discovered preset case runtime."""

    fallback_case_id = "ai_training_dataset_trade"

    def get_runtime_capabilities(self) -> dict[str, Any]:
        settings = get_settings()
        return {
            "supports_controlled_case_runtime": True,
            "supports_uploaded_material_diagnostic": False,
            "supports_real_autojudge": bool(settings.enable_real_autojudge),
            "supports_sse_progress": True,
            "modifies_chroma": False,
            "modifies_neo4j": False,
            "modifies_current_backend": False,
            "local_neural_reranker_enabled": False,
            "uploaded_material_usage": "preview_only/intake_only",
        }

    def adapter_status(self) -> str:
        settings = get_settings()
        if settings.enable_runtime and settings.runtime_mode == "controlled":
            return "partially_connected"
        return "not_configured_or_disabled"

    def can_run_controlled_runtime(self) -> bool:
        settings = get_settings()
        return bool(settings.enable_runtime and settings.runtime_mode == "controlled")

    def plan(self, runtime_mode: RuntimeMode) -> dict:
        return {
            "runtime_mode": runtime_mode,
            "runtime_enabled": get_settings().enable_runtime,
            "controlled_runtime_available": self.can_run_controlled_runtime(),
            "real_multi_agent_runtime_enabled": self.can_run_controlled_runtime(),
            "adapter_status": self.adapter_status(),
            "runtime_capabilities": self.get_runtime_capabilities(),
            "will_modify_current_backend_json": False,
            "will_rebuild_chroma": False,
            "will_clear_or_rebuild_neo4j": False,
            "will_enable_local_neural_reranker": False,
            "boundary_flags": BOUNDARY_FLAGS,
        }

    def select_case_id(self, user_prompt: str) -> str:
        case_ids = self._full18_case_ids()
        for case_id in case_ids:
            if case_id in user_prompt:
                return case_id
        match = re.search(r"case_id\s*[:=]\s*([a-z0-9_]+)", user_prompt, re.IGNORECASE)
        if match and match.group(1) in case_ids:
            return match.group(1)
        return self.fallback_case_id

    def run_controlled_case_runtime(
        self,
        job_id: str,
        user_prompt: str,
        file_previews: list[dict[str, Any]],
        assessment_type: str,
        storage: RuntimeStorage | None = None,
    ) -> dict[str, str]:
        if not self.can_run_controlled_runtime():
            raise RuntimeError("runtime_adapter_not_configured")

        project_root = get_settings().project_root.resolve()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        case_id = self.select_case_id(user_prompt)
        from core.v12.structured_mainline import run_structured_preflight_case

        result = run_structured_preflight_case(
            case_id,
            facts={
                "case_id": case_id,
                "assessment_type": assessment_type,
                "__runtime_options__": {
                    "bge_m3_enabled": False,
                    "local_neural_reranker_enabled": False,
                },
            },
        )

        storage = storage or RuntimeStorage()
        artifacts_dir = storage.artifacts_dir(job_id)
        manifest = {
            "runtime_mode": "controlled_case_runtime_real",
            "adapter_status": self.adapter_status(),
            "case_id": case_id,
            "assessment_type": assessment_type,
            "uploaded_material_usage": "preview_only",
            "uploaded_material_runtime_supported": False,
            "controlled_case_runtime_supported": True,
            "source_backed_claim_fabricated": False,
            "manual_verified_claim_fabricated": False,
            "article_level_verified_claim_fabricated": False,
            "formal_legal_opinion_claim": False,
            "local_neural_reranker_enabled": False,
            "uploaded_files_written_to_chroma": False,
            "uploaded_files_written_to_neo4j": False,
            "current_backend_modified": False,
        }
        payloads: dict[str, Any] = {
            "runtime_result.json": result,
            "evidence_pack.json": result.get("evidence_pack", {}),
            "citation_plan.json": {"citations": result.get("citations", [])},
            "source_trace.json": {"evidence": result.get("evidence", []), "source_trace_caveat": "not_manual_verification"},
            "retrieval_trace.json": {
                "retrieval_trace": result.get("retrieval_trace", []),
                "runtime_options": result.get("runtime_options", {}),
                "bge_m3": "disabled_for_controlled_smoke",
                "local_neural_reranker": "disabled_by_default",
            },
            "score.json": {
                "case_preflight_pass": result.get("case_preflight_pass"),
                "failed_items": result.get("failed_items", []),
                "warning_items": result.get("warning_items", []),
                "autojudge_score_not_run": not get_settings().enable_real_autojudge,
            },
            "autojudge_result.json": result.get("autojudge_envelope", {}),
            "llm_judge_result.json": {"state": "not_run", "reason": "BE3 controlled smoke does not fabricate LLM judge."},
            "runtime_manifest.json": manifest,
            "input_materials_manifest.json": {
                "user_prompt": user_prompt,
                "file_previews": file_previews,
                "uploaded_material_usage": "preview_only",
            },
        }
        rel_paths: dict[str, str] = {}
        for name, payload in payloads.items():
            path = artifacts_dir / name
            write_json_atomic(path, payload if isinstance(payload, dict) else {"value": payload})
            rel_paths[name] = storage.display_path(path)

        report_path = artifacts_dir / "report.md"
        report_text = str(result.get("rendered_report") or "# Runtime report missing\n")
        report_path.write_text(
            report_text
            + "\n\n---\nPrototype diagnostic only. Not a formal legal opinion. Source trace is not manual verification.\n",
            encoding="utf-8",
        )
        rel_paths["report.md"] = storage.display_path(report_path)

        expected = {
            "runtime_result.json",
            "report.md",
            "evidence_pack.json",
            "citation_plan.json",
            "source_trace.json",
            "retrieval_trace.json",
            "score.json",
            "autojudge_result.json",
            "llm_judge_result.json",
            "runtime_manifest.json",
            "input_materials_manifest.json",
        }
        missing = sorted(expected - set(rel_paths))
        missing_path = artifacts_dir / "missing_artifacts.json"
        write_json_atomic(missing_path, {"missing_artifacts": missing})
        rel_paths["missing_artifacts.json"] = storage.display_path(missing_path)
        return rel_paths

    def _full18_case_ids(self) -> list[str]:
        project_root = get_settings().project_root.resolve()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        try:
            from core.v12.mainline_case_registry import full18_case_ids

            return full18_case_ids()
        except Exception:
            return [self.fallback_case_id]
