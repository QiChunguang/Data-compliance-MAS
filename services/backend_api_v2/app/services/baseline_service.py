from __future__ import annotations

from typing import Any, Dict

from app.core.boundaries import BOUNDARY_FLAGS, IMMUTABILITY_RULES
from app.core.project_paths import get_project_paths
from app.data.phase11_2_case_baseline import PHASE11_2_CASE_BASELINE
from app.services.file_io import file_status, read_json_if_exists, read_text_if_exists


class BaselineService:
    def status(self) -> Dict[str, Any]:
        paths = get_project_paths()
        current_backend = read_json_if_exists(paths.current_backend_json)
        case_count = len(PHASE11_2_CASE_BASELINE)
        ge70 = sum(1 for row in PHASE11_2_CASE_BASELINE if row["ge_70"])
        scores = [row["final_score"] for row in PHASE11_2_CASE_BASELINE]
        return {
            "phase": "Phase12-BackendGreenfieldApiShellAndFrontendSelectiveRefactor",
            "baseline_phase": "Phase11.3",
            "authoritative_validation_phase": "Phase11.2",
            "validation_status": "pass_with_warnings / completed",
            "full18_completed": "18/18",
            "strict_autojudge_completed": "18/18",
            "real_llm_judge_completed": "18/18",
            "case_count_score_ge_70": f"{ge70}/{case_count}",
            "score_mean": round(sum(scores) / len(scores), 2),
            "score_min": min(scores),
            "score_max": max(scores),
            "boundary_flags": BOUNDARY_FLAGS,
            "immutability_rules": IMMUTABILITY_RULES,
            "current_backend_json": current_backend,
            "paths": paths.as_dict(),
            "file_status": {
                "project_root": {"path": str(paths.project_root), "exists": paths.project_root.exists()},
                "full18_run_root": {"path": str(paths.full18_run_root), "exists": paths.full18_run_root.exists()},
                "current_backend_json": file_status(paths.current_backend_json),
                "active_chroma_run_dir_expected": {"path": str(paths.active_chroma_run_dir_expected), "exists": paths.active_chroma_run_dir_expected.exists()},
                "phase11_2_report": file_status(paths.phase11_2_report),
                "phase11_3_project_report": file_status(paths.phase11_3_project_report),
                "phase11_3_eval_report": file_status(paths.phase11_3_eval_report),
            },
            "warnings": [
                "API is diagnostic/prototype-oriented; do not present as formal legal opinion.",
                "BGE-M3 full18 status remains partially_effective.",
                "Local neural reranker is diagnostic_only and disabled by default.",
                "Do not hide low scores, evidence gaps, CAP reasons, or source-trace caveats in frontend.",
            ],
        }

    def reports(self) -> Dict[str, Any]:
        paths = get_project_paths()
        return {
            "project_baseline_report": {
                "path": str(paths.phase11_3_project_report),
                "content": read_text_if_exists(paths.phase11_3_project_report),
                "status": file_status(paths.phase11_3_project_report),
            },
            "evaluation_system_baseline_report": {
                "path": str(paths.phase11_3_eval_report),
                "content": read_text_if_exists(paths.phase11_3_eval_report),
                "status": file_status(paths.phase11_3_eval_report),
            },
        }
