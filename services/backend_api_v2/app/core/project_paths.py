from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from app.core.config import get_settings


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    full18_run_root: Path
    reports_dir: Path
    manifests_dir: Path
    current_backend_json: Path
    active_chroma_run_dir_expected: Path
    phase11_2_report: Path
    phase11_3_project_report: Path
    phase11_3_eval_report: Path
    runtime_storage_root: Path

    def case_dir(self, case_id: str) -> Path:
        return self.full18_run_root / case_id

    def as_dict(self) -> Dict[str, str]:
        return {
            "project_root": str(self.project_root),
            "full18_run_root": str(self.full18_run_root),
            "reports_dir": str(self.reports_dir),
            "manifests_dir": str(self.manifests_dir),
            "current_backend_json": str(self.current_backend_json),
            "active_chroma_run_dir_expected": str(self.active_chroma_run_dir_expected),
            "phase11_2_report": str(self.phase11_2_report),
            "phase11_3_project_report": str(self.phase11_3_project_report),
            "phase11_3_eval_report": str(self.phase11_3_eval_report),
            "runtime_storage_root": str(self.runtime_storage_root),
        }


def get_project_paths() -> ProjectPaths:
    settings = get_settings()
    root = settings.project_root.resolve()
    full18 = Path(settings.full18_run_root)
    if not full18.is_absolute():
        full18 = root / full18
    return ProjectPaths(
        project_root=root,
        full18_run_root=full18,
        reports_dir=root / "case_validation_v12" / "reports",
        manifests_dir=root / "case_validation_v12" / "manifests",
        current_backend_json=root / "legal_data" / "3.文件分类" / "vector_backends_k14a_clean" / "current_backend.json",
        active_chroma_run_dir_expected=root / "legal_data" / "3.文件分类" / "vector_backends_k14a_clean" / "chroma_split" / "run__clean_primary_authority_no_foreign_5db2a1",
        phase11_2_report=root / "case_validation_v12" / "reports" / "phase11_2_final_mainline_repair_report.md",
        phase11_3_project_report=root / "case_validation_v12" / "reports" / "phase11_3_project_baseline_report.md",
        phase11_3_eval_report=root / "case_validation_v12" / "reports" / "phase11_3_evaluation_system_baseline_report.md",
        runtime_storage_root=(
            Path(settings.runtime_storage_root)
            if Path(settings.runtime_storage_root).is_absolute()
            else root / "services" / "backend_api_v2" / settings.runtime_storage_root
        ),
    )
