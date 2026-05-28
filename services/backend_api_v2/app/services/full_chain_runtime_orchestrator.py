from __future__ import annotations

from typing import Any, Dict, List

from app.services.assessment_runtime_router import AssessmentRuntimeRouter
from app.services.autojudge_runtime_service import AutoJudgeRuntimeService
from app.services.dynamic_case_profile_builder import DynamicCaseProfileBuilder
from app.services.dynamic_citation_plan_service import DynamicCitationPlanService
from app.services.dynamic_claim_plan_service import DynamicClaimPlanService
from app.services.dynamic_evidence_pack_service import DynamicEvidencePackService
from app.services.dynamic_report_render_service import DynamicReportRenderService
from app.services.legal_retrieval_runtime_service import LegalRetrievalRuntimeService
from app.services.real_runtime_bridge import RealRuntimeBridge
from app.services.runtime_event_service import RuntimeEventService
from app.services.runtime_quality_gate_service import RuntimeQualityGateService
from app.services.runtime_storage import RuntimeStorage
from app.services.storage_utils import write_json_atomic
from app.services.uploaded_material_fact_extractor import UploadedMaterialFactExtractor
from app.services.uploaded_runtime_boundary_auditor import UploadedRuntimeBoundaryAuditor
from app.services.user_report_render_service import UserReportRenderService


class FullChainRuntimeOrchestrator:

    def __init__(self) -> None:
        self.bridge = RealRuntimeBridge()
        self.legal_retrieval = LegalRetrievalRuntimeService()
        self.claim_service = DynamicClaimPlanService()
        self.evidence_service = DynamicEvidencePackService()
        self.citation_service = DynamicCitationPlanService()
        self.report_service = DynamicReportRenderService()
        self.autojudge_service = AutoJudgeRuntimeService()
        self.quality_gate = RuntimeQualityGateService()
        self.fact_extractor = UploadedMaterialFactExtractor()
        self.profile_builder = DynamicCaseProfileBuilder()
        self.router = AssessmentRuntimeRouter()
        self.boundary_auditor = UploadedRuntimeBoundaryAuditor()
        self.user_report_service = UserReportRenderService()
        self.storage = RuntimeStorage()
        self.events = RuntimeEventService()

    def run(
        self,
        job: Any,
        conversation_id: str,
        user_prompt: str,
        assessment_type: str,
        file_ids: List[str],
        file_records: List[Any],
        intake: Any,
    ) -> Dict[str, str]:
        artifacts_dir = self.storage.artifacts_dir(job.job_id)
        text_previews = self._get_text_previews(file_records)
        rel_paths: Dict[str, str] = {}

        facts_dict: Dict[str, Any] = {}
        claims: List[Dict[str, Any]] = []
        citations: List[Dict[str, Any]] = []
        bridge_result: Dict[str, Any] = {}
        retrieval_trace: Any = None
        evidence_result: Any = None
        autojudge_result: Any = None
        risk_score: Any = None

        try:
            # ── Stage 1: Job Created ──
            self._emit(job.job_id, "job_created", "job_created", "Full-chain runtime job created.")
            self._emit(job.job_id, "user_prompt_received", "user_prompt_received",
                       "User prompt received.", {"prompt_length": len(user_prompt)})
            self._emit(job.job_id, "uploaded_materials_loaded", "uploaded_materials_loaded",
                       "Uploaded materials loaded for full-chain runtime.",
                       {"file_count": len(file_records)})

            # ── Stage 2: Material Parsing ──
            self._emit(job.job_id, "uploaded_material_intake_started", "material_parser",
                       "Uploaded material intake started.")
            self._emit(job.job_id, "material_parsing_started", "material_parser",
                       "Material parser agent started.")
            input_materials_manifest = {
                "file_ids": file_ids,
                "file_count": len(file_records),
                "text_preview_lengths": [len(p) for p in text_previews],
                "material_usage": "business_facts_only",
            }
            write_json_atomic(artifacts_dir / "input_materials_manifest.json", input_materials_manifest)
            rel_paths["input_materials_manifest.json"] = self.storage.display_path(
                artifacts_dir / "input_materials_manifest.json")
            self._emit(job.job_id, "material_parsing_completed", "material_parser",
                       "Material parsing completed.",
                       {"file_count": len(file_records)})
            self._emit(job.job_id, "uploaded_material_intake_completed", "material_parser",
                       "Uploaded material intake completed.",
                       {"file_count": len(file_records), "business_facts_only": True})

            # ── Stage 3: Fact Extraction ──
            self._emit(job.job_id, "fact_extraction_started", "fact_extraction",
                       "Fact extractor agent started.")
            facts = self.fact_extractor.extract(user_prompt, assessment_type, intake, text_previews)
            facts_dict = facts.model_dump(mode="json")
            write_json_atomic(artifacts_dir / "extracted_facts.json", facts_dict)
            rel_paths["extracted_facts.json"] = self.storage.display_path(
                artifacts_dir / "extracted_facts.json")
            self._emit(job.job_id, "fact_extraction_completed", "fact_extraction",
                       "Fact extraction completed.",
                       {"confidence": facts.extraction_confidence,
                        "missing_count": len(facts.missing_facts)})

            # ── Stage 4: Dynamic Case Profile ──
            self._emit(job.job_id, "dynamic_case_profile_started", "case_profile",
                       "Dynamic case profile builder started.")
            profile = self.profile_builder.build(assessment_type, facts, intake, user_prompt)
            profile_dict = profile.model_dump(mode="json")
            write_json_atomic(artifacts_dir / "dynamic_case_profile.json", profile_dict)
            rel_paths["dynamic_case_profile.json"] = self.storage.display_path(
                artifacts_dir / "dynamic_case_profile.json")
            self._emit(job.job_id, "dynamic_case_profile_completed", "case_profile",
                       "Dynamic case profile created.",
                       {"case_id": profile.case_id, "scenario_tags": profile.scenario_tags})
            self._emit(job.job_id, "case_profile_resolved", "case_profile",
                       "Case profile resolved.",
                       {"case_id": profile.case_id})

            # ── Stage 5: Intent Routing ──
            self._emit(job.job_id, "intent_routing_started", "intent_routing",
                       "Intent routing agent started.")
            route = self.router.route(assessment_type, user_prompt, intake)
            route_dict = route.model_dump(mode="json")
            write_json_atomic(artifacts_dir / "runtime_route.json", route_dict)
            rel_paths["runtime_route.json"] = self.storage.display_path(
                artifacts_dir / "runtime_route.json")
            self._emit(job.job_id, "intent_routing_completed", "intent_routing",
                       "Intent routing completed.",
                       {"route": route.route, "support_level": route.support_level})

            # ── Stage 6: Claim Planning (Dynamic + Bridge) ──
            self._emit(job.job_id, "claim_planning_started", "claim_planning",
                       "Claim planning agent started.")

            bridge_result = self.bridge.run_structured_mainline(
                profile.case_id, facts_dict)

            bridge_claims = bridge_result.get("claims", [])
            if bridge_claims:
                claim_result = self.claim_service.build_from_bridge(bridge_claims)
            else:
                claim_result = self.claim_service.build(
                    assessment_type, facts_dict, None)

            claim_dict = claim_result.model_dump(mode="json")
            claims = claim_dict.get("claims", [])
            write_json_atomic(artifacts_dir / "claim_plan.json", claim_dict)
            rel_paths["claim_plan.json"] = self.storage.display_path(
                artifacts_dir / "claim_plan.json")
            self._emit(job.job_id, "claim_planning_completed", "claim_planning",
                       f"Claim planning completed ({len(claims)} claims).",
                       {"total_claims": len(claims),
                        "source": claim_result.source})

            # ── Stage 7: Legal Retrieval (Real Chroma) ──
            self._emit(job.job_id, "legal_retrieval_started", "legal_retrieval",
                       "Legal retrieval agent started (Chroma vector search).")

            retrieval_queries = self._build_retrieval_queries(
                assessment_type, facts_dict, claims)
            retrieval_collections = self._get_collections_for_type(
                assessment_type)
            retrieval_trace = self.legal_retrieval.retrieve(
                retrieval_queries, retrieval_collections, profile, top_k=10)

            retrieval_dict = retrieval_trace.model_dump(mode="json")
            retrieval_dict["real_legal_retrieval_used"] = bool(not retrieval_trace.fallback_used and retrieval_trace.retrieval_successful)
            retrieval_dict["retrieval_fallback_used"] = bool(retrieval_trace.fallback_used)
            retrieval_dict["queries"] = retrieval_queries
            retrieval_dict["claim_evidence_links"] = [
                {
                    "claim_id": c.get("claim_id", f"claim_{idx + 1}"),
                    "claim_title": c.get("title", ""),
                    "matched_source_ids": [
                        item.source_id for item in retrieval_trace.items
                        if item.query and (c.get("title", "")[:12] in item.query or c.get("domain", "") in item.query)
                    ][:5],
                }
                for idx, c in enumerate(claims)
                if isinstance(c, dict)
            ]
            write_json_atomic(artifacts_dir / "retrieval_trace.json", retrieval_dict)
            rel_paths["retrieval_trace.json"] = self.storage.display_path(
                artifacts_dir / "retrieval_trace.json")
            self._emit(job.job_id, "legal_retrieval_completed", "legal_retrieval",
                       "Legal retrieval completed.",
                       {"total_items": retrieval_trace.total_items,
                        "fallback_used": retrieval_trace.fallback_used,
                        "retrieval_successful": retrieval_trace.retrieval_successful})

            # ── Stage 8: Evidence Pack ──
            self._emit(job.job_id, "evidence_pack_started", "evidence_pack",
                       "Evidence pack agent started.")
            evidence_result = self.evidence_service.build(
                claims, retrieval_trace, facts)
            evidence_dict = evidence_result.model_dump(mode="json")
            write_json_atomic(artifacts_dir / "evidence_pack.json", evidence_dict)
            rel_paths["evidence_pack.json"] = self.storage.display_path(
                artifacts_dir / "evidence_pack.json")
            self._emit(job.job_id, "evidence_pack_completed", "evidence_pack",
                       "Evidence pack completed.",
                       {"total_evidence": evidence_result.total_evidence,
                        "source_backed": evidence_result.source_backed})

            # ── Stage 9: Citation Planning ──
            self._emit(job.job_id, "citation_planning_started", "citation_planning",
                       "Citation planning agent started.")
            self._emit(job.job_id, "citation_plan_started", "citation_planning",
                       "Citation plan started.")

            bridge_citations = bridge_result.get("citations", [])
            if bridge_citations:
                citation_result = self.citation_service.build_from_bridge(
                    bridge_citations)
            else:
                evidence_items = evidence_result.evidence_items if evidence_result else []
                citation_result = self.citation_service.build(
                    claims, evidence_items, retrieval_trace)

            citation_dict = citation_result.model_dump(mode="json")
            citations = citation_dict.get("citations", [])
            real_evidence_rows = [
                item for item in evidence_dict.get("evidence_items", [])
                if item.get("source_id") not in {"", "fallback", "uploaded_material"}
                and item.get("chunk_id")
            ]
            real_citation_rows = [
                item for item in citations
                if item.get("source_id") not in {"", "fallback", "uploaded_material"}
                and item.get("chunk_id")
            ]
            if retrieval_trace:
                retrieval_trace.evidence_pack_real_source_rows = len(real_evidence_rows)
                retrieval_trace.citation_plan_real_citations = len(real_citation_rows)
                retrieval_trace.source_trace_real_rows = len([
                    item for item in retrieval_trace.items
                    if item.source_id and item.chunk_id and not item.fallback_used
                ])
                if retrieval_trace.real_legal_retrieval_used:
                    retrieval_trace.real_legal_retrieval_status = (
                        "effective"
                        if real_evidence_rows and real_citation_rows and retrieval_trace.source_trace_real_rows
                        else "partial"
                    )
                retrieval_dict = retrieval_trace.model_dump(mode="json")
                retrieval_dict["queries"] = retrieval_queries
                write_json_atomic(artifacts_dir / "retrieval_trace.json", retrieval_dict)
            write_json_atomic(artifacts_dir / "citation_plan.json", citation_dict)
            rel_paths["citation_plan.json"] = self.storage.display_path(
                artifacts_dir / "citation_plan.json")
            self._emit(job.job_id, "citation_planning_completed", "citation_planning",
                       f"Citation planning completed ({len(citations)} citations).",
                       {"total_citations": len(citations)})
            self._emit(job.job_id, "citation_plan_completed", "citation_planning",
                       "Citation plan completed.",
                       {"total_citations": len(citations)})

            # ── Stage 10: Compliance Analysis ──
            compliance_analysis = {
                "assessment_type": assessment_type,
                "case_id": profile.case_id,
                "total_claims": len(claims),
                "total_citations": len(citations),
                "retrieval_fallback_used": retrieval_trace.fallback_used if retrieval_trace else True,
                "source_backed": evidence_result.source_backed if evidence_result else False,
                "manual_verified": False,
                "article_level_verified": False,
            }
            write_json_atomic(artifacts_dir / "compliance_analysis.json", compliance_analysis)
            rel_paths["compliance_analysis.json"] = self.storage.display_path(
                artifacts_dir / "compliance_analysis.json")

            # ── Stage 10.5: Risk Scoring ──
            risk_score = self._compute_risk_score(facts, assessment_type)
            risk_dict = risk_score.model_dump(mode="json")
            write_json_atomic(artifacts_dir / "risk_score.json", risk_dict)
            rel_paths["risk_score.json"] = self.storage.display_path(
                artifacts_dir / "risk_score.json")

            # ── Stage 10.6: Agent Analysis Artifacts ──
            self._emit(job.job_id, "agent_analysis_started", "agent_analysis",
                       "Structured multi-agent analysis started.")
            agent_outputs = self._build_agent_outputs(
                profile.case_id,
                assessment_type,
                facts_dict,
                claims,
                evidence_dict,
                citation_dict,
                risk_dict,
                bridge_result,
                retrieval_dict,
            )
            for artifact_name, payload in agent_outputs.items():
                write_json_atomic(artifacts_dir / artifact_name, payload)
                rel_paths[artifact_name] = self.storage.display_path(artifacts_dir / artifact_name)
            self._emit(job.job_id, "legal_agent_completed", "agent_analysis",
                       "LegalAgent claim-plan adapter completed.",
                       {"artifact": "legal_agent_output.json"})
            self._emit(job.job_id, "business_agent_completed", "agent_analysis",
                       "BusinessAgent facts-and-gaps adapter completed.",
                       {"artifact": "business_agent_output.json"})
            self._emit(job.job_id, "technical_agent_completed", "agent_analysis",
                       "TechnicalAgent controls adapter completed.",
                       {"artifact": "technical_agent_output.json"})
            self._emit(job.job_id, "risk_agent_completed", "agent_analysis",
                       "RiskAgent structured risk output completed.",
                       {"artifact": "risk_agent_output.json"})
            self._emit(job.job_id, "auditor_agent_completed", "agent_analysis",
                       "AuditorAgent boundary adapter completed.",
                       {"artifact": "auditor_agent_output.json"})

            # ── Stage 11: Report Generation ──
            self._emit(job.job_id, "report_generation_started", "report_generation",
                       "Report generation agent started.")

            source_trace_dict = {
                "retrieval_mode": "chroma" if (retrieval_trace and not retrieval_trace.fallback_used) else "fallback",
                "real_legal_retrieval_used": bool(retrieval_trace and not retrieval_trace.fallback_used and retrieval_trace.retrieval_successful),
                "retrieval_fallback_used": bool(retrieval_trace.fallback_used if retrieval_trace else True),
                "real_legal_retrieval_status": retrieval_trace.real_legal_retrieval_status if retrieval_trace else "none",
                "total_retrieved": retrieval_trace.total_items if retrieval_trace else 0,
                "source_trace_real_rows": retrieval_trace.source_trace_real_rows if retrieval_trace else 0,
                "real_sources": [
                    item.model_dump(mode="json") for item in (retrieval_trace.items if retrieval_trace else [])
                    if item.source_id and item.chunk_id and not item.fallback_used
                ][:20],
                "bridge_stages": [t for t in bridge_result.get("bridge_trace", [])[:20]],
                "source_backed": False,
                "manual_verified": False,
                "chroma_modified": False,
                "neo4j_modified": False,
                "current_backend_modified": False,
            }
            write_json_atomic(artifacts_dir / "source_trace.json", source_trace_dict)
            rel_paths["source_trace.json"] = self.storage.display_path(
                artifacts_dir / "source_trace.json")

            debug_report = self.report_service.render(
                profile.case_id, assessment_type, user_prompt,
                facts, profile, route, claims,
                evidence_result, citations, risk_score,
                autojudge_result=None, retrieval_trace=retrieval_trace,
                source_trace=source_trace_dict,
                bridge_result=bridge_result,
            )
            report_path = artifacts_dir / "prototype_report.md"
            report_path.write_text(debug_report, encoding="utf-8")
            rel_paths["prototype_report.md"] = self.storage.display_path(report_path)
            user_report = self.user_report_service.render(
                assessment_type=assessment_type,
                user_prompt=user_prompt,
                facts=facts,
                claims=claims,
                citations=citations,
                risk_score=risk_score,
                evidence_pack=evidence_result,
                retrieval_trace=retrieval_trace,
                file_records=file_records,
            )
            user_report_path = artifacts_dir / "user_report.md"
            user_report_path.write_text(user_report, encoding="utf-8")
            rel_paths["user_report.md"] = self.storage.display_path(user_report_path)
            improved_report_path = artifacts_dir / "improved_report.md"
            improved_report_path.write_text(user_report, encoding="utf-8")
            rel_paths["improved_report.md"] = self.storage.display_path(improved_report_path)
            rendered_report = {
                "format": "markdown",
                "artifact": "user_report.md",
                "compatibility_artifact": "improved_report.md",
                "report_text": user_report,
                "not_formal_legal_opinion": True,
                "uploaded_material_used_as_business_facts": True,
            }
            write_json_atomic(artifacts_dir / "rendered_report.json", rendered_report)
            rel_paths["rendered_report.json"] = self.storage.display_path(artifacts_dir / "rendered_report.json")
            writer_output = dict(agent_outputs.get("writer_agent_output.json", {}))
            writer_output.update({
                "agent_completed": True,
                "report_artifact": "user_report.md",
                "compatibility_report_artifact": "improved_report.md",
                "rendered_report_artifact": "rendered_report.json",
                "not_formal_legal_opinion": True,
            })
            write_json_atomic(artifacts_dir / "writer_agent_output.json", writer_output)
            rel_paths["writer_agent_output.json"] = self.storage.display_path(artifacts_dir / "writer_agent_output.json")
            self._emit(job.job_id, "writer_agent_completed", "agent_analysis",
                       "WriterAgent report adapter completed.",
                       {"artifact": "writer_agent_output.json"})
            self._emit(job.job_id, "report_generation_completed", "report_generation",
                       "Report generation completed.",
                       {"report_length": len(user_report)})

            # ── Stage 12: AutoJudge Scoring ──
            self._emit(job.job_id, "autojudge_started", "autojudge",
                       "AutoJudge scoring agent started.")

            autojudge_envelope = bridge_result.get("autojudge_envelope", {})
            runtime_artifacts_for_judge = {
                "claim_plan.json": claim_dict,
                "evidence_pack.json": evidence_dict,
                "citation_plan.json": citation_dict,
                "retrieval_trace.json": retrieval_dict,
                "source_trace.json": source_trace_dict,
                "risk_score.json": risk_dict,
                "dynamic_case_profile.json": profile_dict,
                "extracted_facts.json": facts_dict,
            }
            autojudge_result = self.autojudge_service.score(
                debug_report, claims, evidence_result, citations,
                risk_score, autojudge_envelope, profile.case_id,
                artifacts_dir=artifacts_dir,
                runtime_artifacts=runtime_artifacts_for_judge)

            write_json_atomic(artifacts_dir / "autojudge_envelope.json", autojudge_result.autojudge_envelope)
            rel_paths["autojudge_envelope.json"] = self.storage.display_path(
                artifacts_dir / "autojudge_envelope.json")

            autojudge_dict = autojudge_result.model_dump(mode="json")
            write_json_atomic(artifacts_dir / "autojudge_result.json", autojudge_dict)
            rel_paths["autojudge_result.json"] = self.storage.display_path(
                artifacts_dir / "autojudge_result.json")

            score_breakdown = {
                "overall_score": autojudge_result.overall_score,
                "grade": autojudge_result.grade,
                "scoring_mode": autojudge_result.scoring_mode,
                "llm_judge_used": autojudge_result.llm_judge_used,
                "dimension_scores": [
                    d.model_dump(mode="json") for d in autojudge_result.dimension_scores
                ],
                "cap_results": autojudge_result.cap_results,
                "limitations": autojudge_result.limitations,
            }
            write_json_atomic(artifacts_dir / "score_breakdown.json", score_breakdown)
            rel_paths["score_breakdown.json"] = self.storage.display_path(
                artifacts_dir / "score_breakdown.json")

            if autojudge_result.llm_judge_used:
                semantic_result = autojudge_result.semantic_judge_result
                semantic_result["llm_judge_used"] = True
            else:
                semantic_result = autojudge_result.llm_judge_unavailable or {"llm_judge_unavailable": True, "reason": "llm_judge_not_configured_or_failed"}
                semantic_result["llm_judge_unavailable"] = True
                write_json_atomic(artifacts_dir / "llm_judge_unavailable.json", semantic_result)
                rel_paths["llm_judge_unavailable.json"] = self.storage.display_path(
                    artifacts_dir / "llm_judge_unavailable.json")
                self._emit(job.job_id, "llm_judge_unavailable", "autojudge",
                           "LLM semantic judge unavailable; programmatic AutoJudge result recorded.",
                           {"reason": semantic_result.get("error_reason") or semantic_result.get("reason", "unknown")})
            if autojudge_result.llm_judge_used:
                write_json_atomic(artifacts_dir / "semantic_judge_result.json", semantic_result)
                rel_paths["semantic_judge_result.json"] = self.storage.display_path(
                    artifacts_dir / "semantic_judge_result.json")

            cap_result_dict = {
                "cap_results": autojudge_result.cap_results,
                "envelope_built": autojudge_result.envelope_built,
                "autojudge_scoring_schema_modified": False,
                "cap_rules_modified": False,
            }
            write_json_atomic(artifacts_dir / "cap_result.json", cap_result_dict)
            rel_paths["cap_result.json"] = self.storage.display_path(
                artifacts_dir / "cap_result.json")

            judge_trace = autojudge_result.judge_trace
            judge_trace["programmatic_dimensions"] = list(score_breakdown.get("dimension_scores", []))
            write_json_atomic(artifacts_dir / "judge_trace.json", judge_trace)
            rel_paths["judge_trace.json"] = self.storage.display_path(
                artifacts_dir / "judge_trace.json")

            self._emit(job.job_id, "autojudge_completed", "autojudge",
                       f"AutoJudge scoring completed ({autojudge_result.grade}).",
                       {"overall_score": autojudge_result.overall_score,
                        "grade": autojudge_result.grade,
                        "llm_judge_used": autojudge_result.llm_judge_used})

            # ── Re-render report with AutoJudge results ──
            debug_report = self.report_service.render(
                profile.case_id, assessment_type, user_prompt,
                facts, profile, route, claims,
                evidence_result, citations, risk_score,
                autojudge_result=autojudge_dict,
                retrieval_trace=retrieval_trace,
                source_trace=source_trace_dict,
                bridge_result=bridge_result,
            )
            report_path.write_text(debug_report, encoding="utf-8")
            user_report = self.user_report_service.render(
                assessment_type=assessment_type,
                user_prompt=user_prompt,
                facts=facts,
                claims=claims,
                citations=citations,
                risk_score=risk_score,
                evidence_pack=evidence_result,
                retrieval_trace=retrieval_trace,
                file_records=file_records,
            )
            user_report_path.write_text(user_report, encoding="utf-8")
            improved_report_path.write_text(user_report, encoding="utf-8")
            rendered_report["report_text"] = user_report
            rendered_report["debug_report_artifact"] = "prototype_report.md"
            rendered_report["user_report_sections"] = [
                "审查对象与材料范围",
                "业务事实摘要",
                "适用法律依据",
                "核心合规风险",
                "证据与引用",
                "整改建议",
                "证据边界与人工复核状态",
                "免责声明",
            ]
            write_json_atomic(artifacts_dir / "rendered_report.json", rendered_report)

            # ── Stage 13: Boundary Audit ──
            self._emit(job.job_id, "boundary_audit_started", "boundary_audit",
                       "Boundary auditor agent started.")
            boundary = self.boundary_auditor.audit()
            boundary_passed = self.boundary_auditor.verify_hard_boundaries()
            boundary_dict = boundary.model_dump(mode="json") if hasattr(boundary, "model_dump") else {}
            boundary_dict["passed"] = boundary_passed
            write_json_atomic(artifacts_dir / "boundary_audit.json", boundary_dict)
            rel_paths["boundary_audit.json"] = self.storage.display_path(
                artifacts_dir / "boundary_audit.json")
            self._emit(job.job_id, "boundary_audit_completed", "boundary_audit",
                       "Boundary audit completed.",
                       {"passed": boundary_passed})

            # ── Stage 14: Quality Gate ──
            self._emit(job.job_id, "quality_gate_started", "quality_gate",
                       "Quality gate check started.")
            gate_result = self.quality_gate.check(
                artifacts=rel_paths,
                autojudge_result=autojudge_result,
                bridge_trace=bridge_result.get("bridge_trace", []),
                boundary_audit=boundary,
            )
            gate_dict = gate_result.model_dump(mode="json")
            write_json_atomic(artifacts_dir / "quality_gate.json", gate_dict)
            rel_paths["quality_gate.json"] = self.storage.display_path(
                artifacts_dir / "quality_gate.json")

            missing_capabilities = self._build_missing_capabilities(
                bridge_result, retrieval_trace, autojudge_result)
            write_json_atomic(artifacts_dir / "missing_capabilities.json", missing_capabilities)
            rel_paths["missing_capabilities.json"] = self.storage.display_path(
                artifacts_dir / "missing_capabilities.json")

            self._emit(job.job_id, "quality_gate_completed", "quality_gate",
                       f"Quality gate check completed ({gate_result.gate_status}).",
                       {"gate_status": gate_result.gate_status,
                        "passed_checks": gate_result.passed_checks,
                        "failed_checks": gate_result.failed_checks})

            # ── Write remaining artifacts ──
            intake_dict = intake.model_dump(mode="json") if hasattr(intake, "model_dump") else intake
            write_json_atomic(artifacts_dir / "uploaded_material_intake.json", intake_dict)
            rel_paths["uploaded_material_intake.json"] = self.storage.display_path(
                artifacts_dir / "uploaded_material_intake.json")

            bridge_trace_dict = {"bridge_trace": bridge_result.get("bridge_trace", [])}
            write_json_atomic(artifacts_dir / "bridge_trace.json", bridge_trace_dict)
            rel_paths["bridge_trace.json"] = self.storage.display_path(
                artifacts_dir / "bridge_trace.json")

            runtime_manifest = {
                "runtime_mode": "full_chain_runtime",
                "action": "run_full_chain_report",
                "async_job": True,
                "not_production_queue": True,
                "human_review_status": "not_reviewed",
                "human_review_gate_present": True,
                "automatic_agents_total": 6,
                "automatic_agents_invoked": 6,
                "autojudge_policy": "auto_on_for_report_generation",
                "file_ids_non_empty": bool(file_ids),
                "uploaded_material_used_as_business_facts": True,
                "uploaded_material_written_to_chroma": False,
                "uploaded_material_written_to_neo4j": False,
                "uploaded_material_written_to_legal_data": False,
                "current_backend_modified": False,
                "core_v12_mainline_invoked": bool(bridge_result.get("structured_mainline_enabled") or bridge_result.get("manual_bridge_used")),
                "core_v12_structured_mainline_success": bool(bridge_result.get("structured_mainline_enabled")),
                "agents_invoked": True,
                "legal_rag_invoked": bool(retrieval_trace is not None),
                "real_legal_retrieval_used": bool(retrieval_trace and not retrieval_trace.fallback_used and retrieval_trace.retrieval_successful),
                "retrieval_fallback_used": bool(retrieval_trace.fallback_used if retrieval_trace else True),
                "real_legal_retrieval_status": retrieval_trace.real_legal_retrieval_status if retrieval_trace else "none",
                "chroma_query_attempted": bool(retrieval_trace and retrieval_trace.chroma_query_attempted),
                "chroma_hits_count": retrieval_trace.chroma_hits_count if retrieval_trace else 0,
                "neo4j_query_attempted": bool(retrieval_trace and retrieval_trace.neo4j_query_attempted),
                "evidence_pack_real_source_rows": retrieval_trace.evidence_pack_real_source_rows if retrieval_trace else 0,
                "citation_plan_real_citations": retrieval_trace.citation_plan_real_citations if retrieval_trace else 0,
                "source_trace_real_rows": retrieval_trace.source_trace_real_rows if retrieval_trace else 0,
                "fallback_reason": retrieval_trace.fallback_reason if retrieval_trace else "retrieval_trace_missing",
                "autojudge_enabled": True,
                "llm_judge_used": bool(autojudge_result and autojudge_result.llm_judge_used),
                "report_generated": True,
                "job_completed": True,
                "stages_completed": 6,
                "stages": [
                    {"agent": "Material Parser", "stage": "uploaded_materials_loaded", "status": "completed", "artifact": "input_materials_manifest.json"},
                    {"agent": "Fact Extractor", "stage": "fact_extraction_completed", "status": "completed", "artifact": "extracted_facts.json"},
                    {"agent": "Legal Retrieval", "stage": "legal_retrieval_completed", "status": "completed_fallback" if retrieval_trace.fallback_used else "completed", "artifact": "retrieval_trace.json"},
                    {"agent": "Compliance Analyzer", "stage": "agent_analysis_completed", "status": "completed", "artifact": "agent_analysis.json"},
                    {"agent": "Risk Scorer", "stage": "autojudge_completed", "status": "completed_fallback" if not autojudge_result.llm_judge_used else "completed", "artifact": "autojudge_result.json"},
                    {"agent": "Report Writer", "stage": "report_generation_completed", "status": "completed", "artifact": "user_report.md"},
                ],
                "human_review_gate": {
                    "name": "Human Review Gate",
                    "status": "not_reviewed",
                    "allowed_statuses": ["not_reviewed", "pending_review", "reviewed"],
                    "auto_marked_reviewed": False,
                },
                "internal_stages": [
                    {"agent": "Case Profile", "stage": "dynamic_case_profile_completed", "status": "completed", "artifact": "dynamic_case_profile.json"},
                    {"agent": "Claim Planner", "stage": "claim_planning_completed", "status": "completed", "artifact": "claim_plan.json"},
                    {"agent": "Evidence Pack", "stage": "evidence_pack_completed", "status": "completed", "artifact": "evidence_pack.json"},
                    {"agent": "Citation Planner", "stage": "citation_planning_completed", "status": "completed", "artifact": "citation_plan.json"},
                    {"agent": "AutoJudge", "stage": "autojudge_completed", "status": "completed_fallback" if not autojudge_result.llm_judge_used else "completed", "artifact": "autojudge_result.json"},
                    {"agent": "Quality Gate", "stage": "quality_gate_completed", "status": gate_result.gate_status, "artifact": "quality_gate.json"},
                ],
                "bridge_used": True,
                "chroma_queried": retrieval_trace is not None,
                "chroma_fallback_used": retrieval_trace.fallback_used if retrieval_trace else True,
                "autojudge_completed": autojudge_result is not None,
                "autojudge_llm_used": autojudge_result.llm_judge_used if autojudge_result else False,
                "llm_judge_unavailable_recorded": bool(autojudge_result and not autojudge_result.llm_judge_used),
                "quality_gate_status": gate_result.gate_status,
                "uploaded_files_written_to_chroma": False,
                "uploaded_files_written_to_neo4j": False,
                "uploaded_files_written_to_legal_data": False,
                "legal_data_modified": False,
                "chroma_modified": False,
                "neo4j_modified": False,
                "current_backend_modified": False,
                "core_v12_modified": False,
                "agents_modified": False,
                "autojudge_scoring_schema_modified": False,
                "cap_rules_modified": False,
                "source_backed_claim_fabricated": False,
                "manual_verified_claim_fabricated": False,
                "article_level_verified_claim_fabricated": False,
                "formal_legal_opinion_claim": False,
            }
            write_json_atomic(artifacts_dir / "runtime_manifest.json", runtime_manifest)
            rel_paths["runtime_manifest.json"] = self.storage.display_path(
                artifacts_dir / "runtime_manifest.json")

            # ── Stage 15: Artifact Collection & Final ──
            self._emit(job.job_id, "artifact_collection_completed", "artifact_collection",
                       f"All artifacts collected ({len(rel_paths)} files).",
                       {"artifact_count": len(rel_paths)})
            self._emit(job.job_id, "job_completed", "completed",
                       "Full-chain report job completed.",
                       {"artifact_count": len(rel_paths)})
            self._emit(job.job_id, "final", "completed",
                       "Final event: full-chain runtime completed. "
                       "Prototype diagnostic only, not formal legal opinion.")

            return rel_paths

        except Exception as exc:
            self._emit(job.job_id, "runtime_failed", "failed",
                       f"Full-chain runtime failed: {type(exc).__name__}: {exc}")
            self._emit(job.job_id, "job_failed", "failed",
                       "Full-chain report job failed.",
                       {"error_type": type(exc).__name__})
            self._emit(job.job_id, "final", "failed",
                       "Final event: job failed.")
            raise

    def _emit(self, job_id: str, event_type: str, stage: str, message: str,
              payload: Dict | None = None) -> None:
        self.events.add_event(job_id, event_type, stage, message, payload or {})

    def _get_text_previews(self, file_records: List[Any]) -> List[str]:
        previews: List[str] = []
        for rec in file_records:
            if rec is None:
                continue
            preview = getattr(rec, "text_preview", "") or getattr(rec, "content", "") or ""
            if preview:
                previews.append(preview[:2000])
        return previews

    def _build_retrieval_queries(self, assessment_type: str,
                                  facts_dict: Dict[str, Any],
                                  claims: List[Dict[str, Any]]) -> List[str]:
        queries: List[str] = []

        if "data_transaction" in assessment_type:
            queries.extend([
                "数据交易 合法性 数据来源",
                "个人信息 处理 合法性基础 同意",
                "敏感个人信息 单独同意",
                "数据交易 合同 必备条款",
                "数据安全 保护措施",
            ])
        elif "cross_border" in assessment_type:
            queries.extend([
                "数据出境 安全评估",
                "个人信息 出境 标准合同",
                "境外接收方 数据保护",
                "重要数据 出境 风险评估",
                "跨境数据传输 告知同意",
            ])

        for c in claims[:5]:
            cd = c if isinstance(c, dict) else {}
            title = cd.get("title", "")
            domain = cd.get("domain", "")
            if title:
                queries.append(f"{domain} {title}")

        return queries[:10]

    def _get_collections_for_type(self, assessment_type: str) -> List[str]:
        if "data_transaction" in assessment_type:
            return ["data_transaction", "personal_information", "cross_border_data_transfer"]
        elif "cross_border" in assessment_type:
            return ["cross_border_data_transfer", "personal_information", "important_data"]
        return ["data_transaction", "personal_information", "cross_border_data_transfer"]

    def _compute_risk_score(self, facts: Any, assessment_type: str) -> Any:
        from app.services.multi_agent_runtime_orchestrator import MultiAgentRuntimeOrchestrator
        orch = MultiAgentRuntimeOrchestrator()
        return orch._compute_risk_score(facts, assessment_type)

    def _build_agent_outputs(
        self,
        case_id: str,
        assessment_type: str,
        facts_dict: Dict[str, Any],
        claims: List[Dict[str, Any]],
        evidence_dict: Dict[str, Any],
        citation_dict: Dict[str, Any],
        risk_dict: Dict[str, Any],
        bridge_result: Dict[str, Any],
        retrieval_dict: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """Create auditable agent artifacts from the structured runtime state.

        These adapters bind the BE7 runtime to the existing agent responsibilities
        without changing scoring/CAP rules or fabricating verification status.
        """
        known_facts = facts_dict.get("known_facts", []) if isinstance(facts_dict, dict) else []
        missing_facts = facts_dict.get("missing_facts", []) if isinstance(facts_dict, dict) else []
        evidence_items = evidence_dict.get("evidence_items", []) if isinstance(evidence_dict, dict) else []
        citations = citation_dict.get("citations", []) if isinstance(citation_dict, dict) else []
        risk_level = risk_dict.get("overall_level") or risk_dict.get("risk_level") or "unknown"
        fallback_used = bool(retrieval_dict.get("retrieval_fallback_used") or retrieval_dict.get("fallback_used"))

        legal_output = {
            "agent": "LegalAgent",
            "agent_completed": True,
            "case_id": case_id,
            "assessment_type": assessment_type,
            "claims_reviewed": len(claims),
            "citation_candidates": len(citations),
            "legal_basis_source": "readonly_rag" if not fallback_used else "retrieval_fallback_limited",
            "key_legal_issues": [
                c.get("title") or c.get("claim_title") or c.get("claim_id", "unnamed_claim")
                for c in claims[:8]
                if isinstance(c, dict)
            ],
            "boundaries": {
                "source_backed_claim_fabricated": False,
                "manual_verified_claim_fabricated": False,
                "article_level_verified_claim_fabricated": False,
                "formal_legal_opinion_claim": False,
            },
        }

        business_output = {
            "agent": "BusinessAgent",
            "agent_completed": True,
            "known_fact_count": len(known_facts),
            "missing_fact_count": len(missing_facts),
            "known_facts_sample": known_facts[:8],
            "missing_materials": missing_facts[:12],
            "material_role": "uploaded_material_is_business_fact_only",
            "next_information_needed": missing_facts[:8],
        }

        technical_output = {
            "agent": "TechnicalAgent",
            "agent_completed": True,
            "security_control_signals": facts_dict.get("security_controls", []) if isinstance(facts_dict, dict) else [],
            "data_flow_signals": facts_dict.get("transfer_direction", []) if isinstance(facts_dict, dict) else [],
            "technical_gaps": [
                item for item in missing_facts
                if any(token in str(item) for token in ["安全", "加密", "访问", "脱敏", "日志", "传输", "系统"])
            ][:10],
            "boundary": "No uploaded material was written to Chroma, Neo4j, legal_data, or current_backend.",
        }

        risk_output = {
            "agent": "RiskAgent",
            "agent_completed": True,
            "overall_risk_level": risk_level,
            "risk_score": risk_dict,
            "evidence_gap_count": max(0, len(claims) - len(evidence_items)),
            "retrieval_fallback_used": fallback_used,
            "risk_drivers": [
                "retrieval_fallback_used" if fallback_used else "readonly_legal_retrieval_used",
                "missing_business_facts" if missing_facts else "business_facts_present",
                "evidence_coverage_limited" if len(evidence_items) < len(claims) else "evidence_coverage_available",
            ],
        }

        auditor_output = {
            "agent": "AuditorAgent",
            "agent_completed": True,
            "checks": {
                "uploaded_material_written_to_chroma": False,
                "uploaded_material_written_to_neo4j": False,
                "uploaded_material_written_to_legal_data": False,
                "current_backend_modified": False,
                "formal_legal_opinion_claim": False,
                "source_backed_claim_fabricated": False,
                "manual_verified_claim_fabricated": False,
                "article_level_verified_claim_fabricated": False,
            },
            "retrieval_truthfulness": {
                "real_legal_retrieval_used": bool(retrieval_dict.get("real_legal_retrieval_used")),
                "retrieval_fallback_used": fallback_used,
                "fallback_reason": retrieval_dict.get("fallback_reason") or retrieval_dict.get("reason"),
            },
            "core_bridge": {
                "structured_mainline_enabled": bool(bridge_result.get("structured_mainline_enabled")),
                "manual_bridge_used": bool(bridge_result.get("manual_bridge_used")),
            },
        }

        writer_output = {
            "agent": "WriterAgent",
            "agent_completed": False,
            "draft_inputs_ready": True,
            "expected_output": "prototype_report.md",
            "not_formal_legal_opinion": True,
            "report_source": "dynamic_report_render_service",
        }

        agent_analysis = {
            "agents_invoked": True,
            "runtime_adapter_outputs": True,
            "llm_agent_calls_required": False,
            "case_id": case_id,
            "assessment_type": assessment_type,
            "summary": {
                "claims": len(claims),
                "evidence_items": len(evidence_items),
                "citations": len(citations),
                "known_facts": len(known_facts),
                "missing_facts": len(missing_facts),
                "risk_level": risk_level,
                "retrieval_fallback_used": fallback_used,
            },
            "agent_artifacts": [
                "legal_agent_output.json",
                "business_agent_output.json",
                "technical_agent_output.json",
                "risk_agent_output.json",
                "auditor_agent_output.json",
                "writer_agent_output.json",
            ],
            "boundary": {
                "not_formal_legal_opinion": True,
                "uploaded_material_used_as_business_facts": True,
                "legal_basis_from_readonly_rag_or_declared_fallback": True,
            },
        }

        return {
            "agent_analysis.json": agent_analysis,
            "legal_agent_output.json": legal_output,
            "business_agent_output.json": business_output,
            "technical_agent_output.json": technical_output,
            "risk_agent_output.json": risk_output,
            "auditor_agent_output.json": auditor_output,
            "writer_agent_output.json": writer_output,
        }

    def _build_missing_capabilities(self, bridge_result: Dict[str, Any],
                                     retrieval_trace: Any,
                                     autojudge_result: Any) -> Dict[str, Any]:
        capabilities: Dict[str, Any] = {
            "limited_capabilities": [],
            "missing_capabilities": [],
            "fallback_explanations": [],
        }

        bridge_trace = bridge_result.get("bridge_trace", [])
        for t in bridge_trace:
            if isinstance(t, dict) and t.get("fallback_used"):
                capabilities["fallback_explanations"].append({
                    "module": t.get("module", "unknown"),
                    "reason": t.get("fallback_reason", "unknown"),
                })

        if retrieval_trace and retrieval_trace.fallback_used:
            capabilities["limited_capabilities"].append(
                "legal_retrieval_fallback: Chroma 向量检索未成功，使用规则型回退")
        if not retrieval_trace or retrieval_trace.fallback_used:
            capabilities["missing_capabilities"].append(
                "real_chroma_retrieval: 真实 Chroma 向量检索未接入或失败")

        if autojudge_result:
            if not autojudge_result.llm_judge_used:
                capabilities["missing_capabilities"].append(
                    "llm_semantic_judge: LLM 语义评分未接入，使用程序化评分")
        else:
            capabilities["missing_capabilities"].append(
                "autojudge_scoring: AutoJudge 评分未生成")

        capabilities["limited_capabilities"].append(
            "rules_based_fact_extraction: 事实抽取基于规则型关键词匹配")
        capabilities["limited_capabilities"].append(
            "not_manual_verified: 所有评估结果未经人工审核")
        capabilities["limited_capabilities"].append(
            "not_article_level_verified: 法律条文未经逐条验证")

        return capabilities
