from __future__ import annotations

from typing import Any, Dict, List

from app.core.boundaries import BOUNDARY_FLAGS
from app.core.project_paths import get_project_paths
from app.services.case_service import CaseService
from app.services.file_io import file_status, read_json_if_exists, read_text_if_exists


JSON_ARTIFACT_NAMES = [
    "rendered_report.json",
    "case_profile.json",
    "normalized_facts.json",
    "claim_plan.json",
    "evidence_pack.json",
    "citation_plan.json",
    "retrieval_trace.json",
    "source_trace.json",
    "strict_semantic_payload.json",
    "strict_autojudge_result.json",
    "llm_semantic_judge.json",
    "score_component_breakdown.json",
]

TEXT_ARTIFACT_NAMES = [
    "improved_report.md",
    "report.md",
]


class ArtifactService:
    def __init__(self) -> None:
        self.case_service = CaseService()

    def artifact_bundle(self, case_id: str) -> Dict[str, Any]:
        paths = get_project_paths()
        case = self.case_service.get_case(case_id)
        case_dir = paths.case_dir(case_id)
        json_artifacts: Dict[str, Any] = {}
        text_artifacts: Dict[str, Any] = {}
        statuses: List[Dict[str, Any]] = []

        for name in JSON_ARTIFACT_NAMES:
            p = case_dir / name
            json_artifacts[name] = read_json_if_exists(p)
            statuses.append(file_status(p))

        for name in TEXT_ARTIFACT_NAMES:
            p = case_dir / name
            text_artifacts[name] = read_text_if_exists(p)
            statuses.append(file_status(p))

        return {
            "case_id": case_id,
            "case_baseline": case,
            "case_dir": str(case_dir),
            "case_dir_exists": case_dir.exists(),
            "boundary_flags": BOUNDARY_FLAGS,
            "json_artifacts": json_artifacts,
            "text_artifacts": text_artifacts,
            "file_status": statuses,
            "missing_files": [s["path"] for s in statuses if not s["exists"]],
            "frontend_display_advice": [
                "Show score component breakdown instead of final_score alone.",
                "Show evidence gaps and missing business materials.",
                "Show not_production_ready/not_source_backed/not_human_reviewed badges persistently.",
                "Never hide low scores or CAP/evidence-boundary explanations.",
            ],
        }

    def report(self, case_id: str) -> Dict[str, Any]:
        paths = get_project_paths()
        case_dir = paths.case_dir(case_id)
        improved = case_dir / "improved_report.md"
        rendered = case_dir / "rendered_report.json"
        return {
            "case_id": case_id,
            "case_dir": str(case_dir),
            "improved_report_markdown": read_text_if_exists(improved),
            "rendered_report_json": read_json_if_exists(rendered),
            "file_status": {
                "improved_report": file_status(improved),
                "rendered_report": file_status(rendered),
            },
            "boundary_flags": BOUNDARY_FLAGS,
        }
