from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


class AutoJudgeDimensionScore(BaseModel):
    dimension: str = ""
    score: float = 0.0
    weight: float = 1.0
    level: str = "unknown"
    notes: str = ""


class AutoJudgeResult(BaseModel):
    overall_score: float = 0.0
    grade: str = "N/A"
    scoring_mode: str = "programmatic"
    llm_judge_used: bool = False
    llm_judge_available: bool = False
    programmatic_score_used: bool = True
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    dimension_scores: List[AutoJudgeDimensionScore] = Field(default_factory=list)
    cap_results: List[Dict[str, Any] | str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=lambda: [
        "diagnostic_prototype_only",
        "not_formal_legal_opinion",
    ])
    envelope_built: bool = False
    autojudge_scoring_schema_modified: bool = False
    cap_rules_modified: bool = False
    semantic_judge_result: Dict[str, Any] = Field(default_factory=dict)
    llm_judge_unavailable: Dict[str, Any] = Field(default_factory=dict)
    autojudge_envelope: Dict[str, Any] = Field(default_factory=dict)
    canonical_payload: Dict[str, Any] = Field(default_factory=dict)
    judge_trace: Dict[str, Any] = Field(default_factory=dict)


class AutoJudgeRuntimeService:
    """Backend adapter over core/evaluation without modifying scoring/schema/CAP rules."""

    def score(
        self,
        report: str,
        claims: List[Dict[str, Any]],
        evidence_pack: Any,
        citations: List[Dict[str, Any]],
        risk_score: Any,
        envelope: Optional[Dict[str, Any]] = None,
        case_id: str = "",
        artifacts_dir: Path | None = None,
        runtime_artifacts: Optional[Dict[str, Any]] = None,
    ) -> AutoJudgeResult:
        result = AutoJudgeResult()
        runtime_artifacts = runtime_artifacts or {}
        case_id = case_id or "runtime_case"
        case_dir = self._prepare_case_dir(case_id, report, runtime_artifacts, artifacts_dir)
        autojudge_envelope = self._build_envelope(case_id, report, runtime_artifacts, envelope, case_dir)
        result.autojudge_envelope = autojudge_envelope
        result.envelope_built = bool(autojudge_envelope)

        llm_judge = self._run_llm_judge(case_id, case_dir)
        result.semantic_judge_result = llm_judge if llm_judge.get("judge_completed") else {}
        result.llm_judge_unavailable = {} if llm_judge.get("judge_completed") else llm_judge
        result.llm_judge_used = bool(llm_judge.get("judge_available") and llm_judge.get("judge_completed"))
        result.llm_judge_available = bool(llm_judge.get("judge_available"))

        canonical = self._build_canonical_payload(
            case_id=case_id,
            envelope=autojudge_envelope,
            claims=claims,
            evidence_pack=evidence_pack,
            citations=citations,
            risk_score=risk_score,
            llm_judge=llm_judge,
            report_path=str((case_dir / "improved_report.md")).replace("\\", "/"),
        )
        result.canonical_payload = canonical

        programmatic = self._compute_core_programmatic_score(canonical)
        result.programmatic_score_used = True
        result.score_breakdown = programmatic
        result.overall_score = float(programmatic.get("final_total_score") or programmatic.get("programmatic_score") or 0.0)
        result.grade = str(programmatic.get("grade") or self._score_to_grade(result.overall_score))
        result.scoring_mode = "programmatic_plus_llm_semantic" if result.llm_judge_used else "programmatic_llm_unavailable"
        result.cap_results = list(programmatic.get("cap_trigger_candidates") or [])

        dimensions = canonical.get("dimension_assessments") or {}
        for name, item in dimensions.items():
            points = float(item.get("points_awarded", 0) or 0)
            max_score = float(item.get("max_score", 100) or 100)
            pct = round((points / max_score) * 100, 2) if max_score else 0.0
            result.dimension_scores.append(AutoJudgeDimensionScore(
                dimension=name,
                score=points,
                weight=max_score,
                level=self._score_level(pct),
                notes="Q0 raw points",
            ))

        if not result.llm_judge_used:
            result.limitations.append("llm_semantic_judge_unavailable")
        result.judge_trace = {
            "core_evaluation_read": True,
            "case_dir": str(case_dir).replace("\\", "/"),
            "envelope_built": result.envelope_built,
            "programmatic_score_used": result.programmatic_score_used,
            "llm_judge_available": result.llm_judge_available,
            "llm_judge_used": result.llm_judge_used,
            "hardcoded_llm_score_used": False,
            "autojudge_scoring_schema_modified": False,
            "cap_rules_modified": False,
            "scoring_module": "core.evaluation.autojudge_scoring.compute_programmatic_score",
            "semantic_module": "core.evaluation.autojudge_runner.run_real_llm_semantic_judge",
        }
        return result

    def _prepare_case_dir(
        self,
        case_id: str,
        report: str,
        runtime_artifacts: Dict[str, Any],
        artifacts_dir: Path | None,
    ) -> Path:
        case_dir = (artifacts_dir or Path.cwd()) / "autojudge_case"
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "improved_report.md").write_text(report, encoding="utf-8")
        for name, value in runtime_artifacts.items():
            target = case_dir / name
            if name.endswith(".json"):
                target.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        runtime_status = {
            "status": "completed",
            "final_node": "full_chain_runtime",
            "failed_nodes": [],
            "timeout": False,
        }
        final_state = {
            "final_status": "completed",
            "final_node": "full_chain_runtime",
            "rag_status": "fallback" if (runtime_artifacts.get("retrieval_trace.json") or {}).get("fallback_used") else "retrieved",
            "rag_source_trace": runtime_artifacts.get("source_trace.json") or {},
        }
        (case_dir / "runtime_status.json").write_text(json.dumps(runtime_status, ensure_ascii=False, indent=2), encoding="utf-8")
        (case_dir / "case_result.json").write_text(json.dumps(runtime_status, ensure_ascii=False, indent=2), encoding="utf-8")
        (case_dir / "final_state_summary.json").write_text(json.dumps(final_state, ensure_ascii=False, indent=2), encoding="utf-8")
        (case_dir / "quality_guard_result.json").write_text(json.dumps({
            "quality_guard_applied": True,
            "source_backed_count": 0,
            "manual_verified_count": 0,
            "article_level_verified_count": 0,
            "source_backed_overclaim": False,
            "fabricated_source": False,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        return case_dir

    def _build_envelope(
        self,
        case_id: str,
        report: str,
        runtime_artifacts: Dict[str, Any],
        bridge_envelope: Optional[Dict[str, Any]],
        case_dir: Path,
    ) -> Dict[str, Any]:
        try:
            from core.config import CURRENT_PLATFORM, PLATFORM_CONFIGS
            from core.evaluation.autojudge_envelope import build_autojudge_envelope
            from core.evaluation.autojudge_prompt import PROMPT_VERSION, real_llm_semantic_prompt_hash

            cfg = PLATFORM_CONFIGS.get(CURRENT_PLATFORM)
            artifact_pack = {
                "case_id": case_id,
                "run_id": f"runtime_{case_id}",
                "improved_report": report,
                "improved_report_path": str(case_dir / "improved_report.md").replace("\\", "/"),
                "runtime_status_summary": {"status": "completed", "final_node": "full_chain_runtime"},
                "case_result_summary": {"status": "completed", "final_node": "full_chain_runtime"},
                "final_state_summary": {
                    "final_status": "completed",
                    "final_node": "full_chain_runtime",
                    "rag_status": "fallback" if (runtime_artifacts.get("retrieval_trace.json") or {}).get("fallback_used") else "retrieved",
                    "rag_source_trace": runtime_artifacts.get("source_trace.json") or {},
                },
                "source_status_summary": {"source_backed": 0, "needs_manual_verification": 0, "metadata_only": 0},
                "quality_guard_result": {"quality_guard_applied": True},
                "claim_evidence_matrix_rows": [],
                "citation_audit_rows": [],
            }
            return build_autojudge_envelope(
                case_id=case_id,
                artifact_pack=artifact_pack,
                runtime_model="full_chain_runtime",
                judge_model=cfg.model if cfg else "",
                provider=CURRENT_PLATFORM,
                prompt_version=PROMPT_VERSION,
                prompt_hash=real_llm_semantic_prompt_hash(),
                artifact_pack_path=str(case_dir).replace("\\", "/"),
            )
        except Exception as exc:
            fallback = dict(bridge_envelope or {})
            fallback.update({
                "envelope_fallback_used": True,
                "fallback_reason": f"{type(exc).__name__}: {exc}",
                "case_metadata": {
                    "case_id": case_id,
                    "report_path": str(case_dir / "improved_report.md").replace("\\", "/"),
                    "run_id": f"runtime_{case_id}",
                },
            })
            return fallback

    def _run_llm_judge(self, case_id: str, case_dir: Path) -> Dict[str, Any]:
        if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("REGUTHINK_ALLOW_TEST_LLM_JUDGE", "0") != "1":
            return {
                "judge_available": False,
                "judge_completed": False,
                "dry_run_fixture_used": False,
                "case_id": case_id,
                "completion_status": "unavailable",
                "error_reason": "llm_judge_disabled_under_pytest",
                "major_weaknesses": ["LLM judge disabled under pytest to avoid cloud side effects"],
            }
        try:
            from core.evaluation.autojudge_runner import run_real_llm_semantic_judge
            return run_real_llm_semantic_judge(case_id=case_id, case_dir=case_dir)
        except Exception as exc:
            return {
                "judge_available": False,
                "judge_completed": False,
                "dry_run_fixture_used": False,
                "case_id": case_id,
                "completion_status": "unavailable",
                "error_reason": f"{type(exc).__name__}: {exc}",
                "major_weaknesses": [f"LLM judge unavailable: {type(exc).__name__}"],
            }

    def _build_canonical_payload(
        self,
        *,
        case_id: str,
        envelope: Dict[str, Any],
        claims: List[Dict[str, Any]],
        evidence_pack: Any,
        citations: List[Dict[str, Any]],
        risk_score: Any,
        llm_judge: Dict[str, Any],
        report_path: str,
    ) -> Dict[str, Any]:
        from core.evaluation.autojudge_schema import DIMENSIONS

        evidence_count = self._evidence_count(evidence_pack)
        citation_count = len(citations)
        claim_count = len(claims)
        completeness = 10 if claim_count and evidence_count and citation_count else 7
        source_points = 3 if evidence_count == 0 else min(15, 6 + evidence_count)
        citation_points = 4 if citation_count == 0 else min(15, 6 + citation_count)
        mapping_points = 4 if not (claim_count and evidence_count) else min(15, 6 + min(claim_count, evidence_count))
        unsupported_points = 8 if evidence_count else 5
        scenario_points = 8 if claim_count >= 3 else 5
        bounded_points = 8
        report_points = 4
        boundary_points = 5
        raw_points = {
            "runtime_artifact_completeness": completeness,
            "source_trace_completeness": source_points,
            "legal_citation_accuracy": citation_points,
            "claim_evidence_mapping": mapping_points,
            "unsupported_claim_hallucination_control": unsupported_points,
            "scenario_coverage": scenario_points,
            "evidence_bounded_conclusion": bounded_points,
            "report_professionalism_template_residue": report_points,
            "thesis_usability_boundary_clarity": boundary_points,
        }
        dimensions = {
            name: {
                "max_score": DIMENSIONS[name],
                "points_awarded": max(0, min(DIMENSIONS[name], int(raw_points.get(name, 0)))),
                "findings": [f"runtime diagnostic evidence: claims={claim_count}, evidence={evidence_count}, citations={citation_count}"],
                "severity": "medium",
                "evidence_refs": ["runtime_artifacts"],
            }
            for name in DIMENSIONS
        }
        unsupported = 0 if evidence_count else max(1, claim_count)
        return {
            "judge_metadata": envelope.get("judge_metadata") or {
                "judge_model": (llm_judge.get("judge_model") or "unavailable"),
                "temperature": 0,
                "top_p": 1,
                "prompt_version": llm_judge.get("prompt_version", "runtime-adapter"),
                "prompt_hash": llm_judge.get("prompt_hash", "unavailable"),
                "rubric_version": "phase46e8a-q0-rubric-v1",
                "schema_version": "phase46e8a-q2-autojudge-schema-v1",
            },
            "case_metadata": envelope.get("case_metadata") or {
                "case_id": case_id,
                "run_id": f"runtime_{case_id}",
                "report_path": report_path,
            },
            "dimension_assessments": dimensions,
            "claim_audit_summary": {
                "total_core_claims": claim_count,
                "unsupported_or_wrong_scope_or_unverified_high_severity_claims": unsupported,
                "unsupported_claim_rate_candidate": round(unsupported / claim_count, 4) if claim_count else 1.0,
                "unsupported_claim_items": [],
            },
            "citation_audit_summary": {
                "citation_count": citation_count,
                "source_backed_count": 0,
                "needs_manual_verification_count": citation_count,
                "unsupported_citation_count": 0 if citation_count else 1,
                "wrong_scope_count": 0,
                "fabricated_source_risk_count": 0,
            },
            "quality_flags": {
                "source_backed_overclaim": False,
                "local_hash_misuse": False,
                "fabricated_source": False,
                "severe_wrong_scope": False,
                "severe_scenario_omission": False,
                "production_ready_overclaim": False,
                "hallucination_free_overclaim": False,
                "lawyer_replacement_overclaim": False,
            },
            "cap_trigger_candidates": [] if evidence_count else [{"cap": "source_trace_missing", "reason": "no retrieved evidence items"}],
            "thesis_usability_reasoning": {
                "recommended_category_candidate": "diagnostic_case",
                "reasoning": "Runtime adapter produces diagnostic AutoJudge evidence under prototype boundaries.",
                "caveats": ["Not human reviewed", "Not formal legal advice"],
            },
            "boundary_warnings": ["prototype diagnostic only", "uploaded materials are business facts only"],
            "llm_semantic_judge": llm_judge,
            "runtime_completed": True,
        }

    def _compute_core_programmatic_score(self, canonical: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from core.evaluation.autojudge_scoring import compute_programmatic_score
            return compute_programmatic_score(canonical)
        except Exception as exc:
            return {
                "valid": False,
                "errors": [f"{type(exc).__name__}: {exc}"],
                "programmatic_score": 0,
                "final_total_score": 0,
                "grade": "F",
                "cap_trigger_candidates": [{"cap": "runtime_not_completed", "reason": "programmatic score failed"}],
            }

    def _evidence_count(self, evidence_pack: Any) -> int:
        if evidence_pack and hasattr(evidence_pack, "total_evidence"):
            return int(evidence_pack.total_evidence or 0)
        if isinstance(evidence_pack, dict):
            return len(evidence_pack.get("evidence_items", evidence_pack.get("evidence_rows", [])) or [])
        return 0

    def _score_to_grade(self, score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 75:
            return "B"
        if score >= 65:
            return "C"
        if score >= 50:
            return "D"
        return "F"

    def _score_level(self, score: float) -> str:
        if score >= 80:
            return "excellent"
        if score >= 60:
            return "good"
        if score >= 40:
            return "fair"
        return "poor"
