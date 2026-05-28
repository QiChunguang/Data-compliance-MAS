from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


class BridgeTrace(BaseModel):
    module: str = ""
    call_attempted: bool = False
    call_successful: bool = False
    error_message: str = ""
    fallback_used: bool = True
    fallback_reason: str = ""
    output_type: str = "fallback"
    core_v12_modified: bool = False
    chroma_accessed: bool = False
    neo4j_accessed: bool = False


class RealRuntimeBridge:
    def __init__(self) -> None:
        self._trace: List[BridgeTrace] = []

    def run_structured_mainline(self, case_id: str, facts: Dict[str, Any]) -> Dict[str, Any]:
        trace = BridgeTrace(module="structured_mainline", call_attempted=True)
        try:
            from core.v12.structured_mainline import run_structured_preflight_case
            result = run_structured_preflight_case(case_id, facts)
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_structured_mainline"
            self._trace.append(trace)
            return result
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 structured_mainline failed: {type(exc).__name__}"
            self._trace.append(trace)
            return self._run_manual_mainline(case_id, facts)

    def resolve_case_profile(self, case_id: str, facts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace = BridgeTrace(module="case_profile_resolver", call_attempted=True)
        try:
            from core.v12.case_profile_resolver import resolve_case_profile
            profile, stage = resolve_case_profile(case_id, facts or {})
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_case_profile"
            self._trace.append(trace)
            return {"profile": profile, "stage_ok": stage.stage_completed}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 case_profile_resolver failed: {type(exc).__name__}"
            self._trace.append(trace)
            return self._build_fallback_profile(case_id, facts or {})

    def normalize_facts(self, case_id: str, facts: Dict[str, Any]) -> Dict[str, Any]:
        trace = BridgeTrace(module="fact_normalizer", call_attempted=True)
        try:
            from core.v12.fact_normalizer import normalize_facts
            normalized, stage = normalize_facts(case_id, facts)
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_normalized_facts"
            self._trace.append(trace)
            return {"normalized": normalized, "stage_ok": stage.stage_completed}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 fact_normalizer failed: {type(exc).__name__}"
            self._trace.append(trace)
            return {"normalized": None, "stage_ok": False, "error": str(exc)}

    def plan_claims(self, profile: Any, normalized: Any) -> Dict[str, Any]:
        trace = BridgeTrace(module="claim_planner", call_attempted=True)
        try:
            from core.v12.claim_planner import plan_claims
            claims, stage = plan_claims(profile, normalized)
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_claims"
            self._trace.append(trace)
            return {"claims": claims, "stage_ok": stage.stage_completed}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 claim_planner failed: {type(exc).__name__}"
            self._trace.append(trace)
            return {"claims": [], "stage_ok": False, "error": str(exc)}

    def retrieve_primary_evidence(
        self, profile: Any, normalized: Any, claims: List[Any], retrieval_options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        trace = BridgeTrace(module="primary_evidence_retriever", call_attempted=True)
        try:
            from core.v12.primary_evidence_retriever import retrieve_primary_evidence
            evidence, stage = retrieve_primary_evidence(
                profile, normalized, claims, retrieval_options=retrieval_options or {}
            )
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_evidence"
            trace.chroma_accessed = True
            self._trace.append(trace)
            return {"evidence": evidence, "stage_ok": stage.stage_completed}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 evidence retriever failed: {type(exc).__name__}"
            self._trace.append(trace)
            return {"evidence": [], "stage_ok": False, "error": str(exc)}

    def plan_citations(self, case_id: str, claims: List[Any], evidence: List[Any]) -> Dict[str, Any]:
        trace = BridgeTrace(module="citation_planner", call_attempted=True)
        try:
            from core.v12.citation_planner import plan_citations
            citations, stage = plan_citations(case_id, claims, evidence)
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_citations"
            self._trace.append(trace)
            return {"citations": citations, "stage_ok": stage.stage_completed}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 citation_planner failed: {type(exc).__name__}"
            self._trace.append(trace)
            return {"citations": [], "stage_ok": False, "error": str(exc)}

    def build_evidence_pack(self, case_id: str, claims: List[Any], evidence: List[Any], citations: List[Any]) -> Dict[str, Any]:
        trace = BridgeTrace(module="evidence_pack_builder", call_attempted=True)
        try:
            from core.v12.evidence_pack_builder import build_evidence_pack
            pack, stage = build_evidence_pack(case_id, claims, evidence, citations)
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_evidence_pack"
            self._trace.append(trace)
            return {"evidence_pack": pack, "stage_ok": stage.stage_completed}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 evidence_pack_builder failed: {type(exc).__name__}"
            self._trace.append(trace)
            return {"evidence_pack": {}, "stage_ok": False, "error": str(exc)}

    def render_report(self, case_id: str, profile: Any, normalized: Any, claims: List[Any],
                      citations: List[Any], evidence_pack: Any, risk_findings: List[Dict]) -> Dict[str, Any]:
        trace = BridgeTrace(module="report_renderer", call_attempted=True)
        try:
            from core.v12.report_renderer import render_report
            report, stage = render_report(case_id, profile, normalized, claims, citations, evidence_pack, risk_findings)
            try:
                from agents.writer_agent import WriterAgent
                report = WriterAgent().polish_report(
                    report,
                    [c.to_row() if hasattr(c, 'to_row') else c for c in citations],
                    evidence_pack,
                )
            except Exception:
                pass
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_report"
            self._trace.append(trace)
            return {"report": report, "stage_ok": stage.stage_completed}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 report_renderer failed: {type(exc).__name__}"
            self._trace.append(trace)
            return {"report": "", "stage_ok": False, "error": str(exc)}

    def build_autojudge_envelope(self, case_id: str, claims: List[Any], citations: List[Any],
                                  evidence_pack: Any, report: str) -> Dict[str, Any]:
        trace = BridgeTrace(module="autojudge_envelope_builder", call_attempted=True)
        try:
            from core.v12.autojudge_envelope_builder import build_autojudge_envelope
            envelope = build_autojudge_envelope(
                case_id,
                [c.__dict__ if hasattr(c, '__dict__') else c for c in claims],
                [c.to_row() if hasattr(c, 'to_row') else c for c in citations],
                evidence_pack,
                report,
            )
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_autojudge_envelope"
            self._trace.append(trace)
            return {"envelope": envelope}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 autojudge_envelope failed: {type(exc).__name__}"
            self._trace.append(trace)
            return {"envelope": {}, "error": str(exc)}

    def audit_mainline(self, case_id: str, profile: Any, claims: List[Any],
                       evidence: List[Any], citations: List[Any], report: str) -> Dict[str, Any]:
        trace = BridgeTrace(module="mainline_auditor", call_attempted=True)
        try:
            from core.v12.mainline_auditor import audit_mainline
            stage = audit_mainline(case_id, profile, claims, evidence, citations, report)
            trace.call_successful = True
            trace.fallback_used = False
            trace.output_type = "core_v12_audit"
            self._trace.append(trace)
            return {"audit_ok": stage.stage_completed, "failed_items": stage.failed_items}
        except Exception as exc:
            trace.error_message = str(exc)
            trace.fallback_reason = f"core/v12 audit_mainline failed: {type(exc).__name__}"
            self._trace.append(trace)
            return {"audit_ok": False, "error": str(exc)}

    def get_trace(self) -> List[Dict[str, Any]]:
        return [t.model_dump(mode="json") for t in self._trace]

    def _run_manual_mainline(self, case_id: str, facts: Dict[str, Any]) -> Dict[str, Any]:
        profile_result = self.resolve_case_profile(case_id, facts)
        normalized_result = self.normalize_facts(case_id, facts)

        profile = profile_result.get("profile")
        normalized = normalized_result.get("normalized")

        claims_result = self.plan_claims(profile, normalized)
        claims = claims_result.get("claims", [])

        evidence_result = self.retrieve_primary_evidence(profile, normalized, claims)
        evidence = evidence_result.get("evidence", [])

        citation_result = self.plan_citations(case_id, claims, evidence)
        citations = citation_result.get("citations", [])

        pack_result = self.build_evidence_pack(case_id, claims, evidence, citations)
        evidence_pack = pack_result.get("evidence_pack", {})

        report_result = self.render_report(case_id, profile, normalized, claims, citations, evidence_pack, [])
        report = report_result.get("report", "")

        envelope_result = self.build_autojudge_envelope(case_id, claims, citations, evidence_pack, report)

        return {
            "case_id": case_id,
            "structured_mainline_enabled": False,
            "manual_bridge_used": True,
            "claims": [c.__dict__ if hasattr(c, '__dict__') else c for c in claims] if claims else [],
            "evidence": [e.to_row() if hasattr(e, 'to_row') else e for e in evidence] if evidence else [],
            "citations": [c.to_row() if hasattr(c, 'to_row') else c for c in citations] if citations else [],
            "evidence_pack": evidence_pack,
            "rendered_report": report,
            "autojudge_envelope": envelope_result.get("envelope", {}),
            "bridge_trace": self.get_trace(),
        }

    def _build_fallback_profile(self, case_id: str, facts: Dict[str, Any]) -> Dict[str, Any]:
        from core.v12.runtime_contracts import CaseProfilePlan

        allowed_collections = []
        if "data_transaction" in case_id:
            allowed_collections = ["data_transaction", "personal_information", "cross_border_data_transfer"]
        elif "cross_border" in case_id:
            allowed_collections = ["cross_border_data_transfer", "personal_information", "important_data"]
        elif "pipl" in case_id:
            allowed_collections = ["personal_information", "sensitive_personal_information"]
        else:
            allowed_collections = ["data_transaction", "personal_information", "cross_border_data_transfer"]

        has_cross_border = bool(facts.get("cross_border_elements") or facts.get("transfer_direction") == "cross_border")
        profile = CaseProfilePlan(
            case_id=case_id,
            graph_case_id=case_id,
            expected_profile=case_id,
            allowed_collections=allowed_collections,
            disallowed_collections=[],
            allowed_source_types=["law", "regulation", "policy", "standard"],
            disallowed_source_types=[],
            allowed_topics=["数据合规", "个人信息保护", "数据交易", "跨境传输"],
            required_evidence_mix=["law_basis", "regulatory_requirement"],
            facts_require_crossborder=has_cross_border,
            facts_support_ai_service_sector=False,
        )
        return {"profile": profile, "stage_ok": True, "fallback_profile": True}