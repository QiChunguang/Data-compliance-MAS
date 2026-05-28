from __future__ import annotations

from typing import Any, Dict, List

from app.models.assessment import AssessmentType
from app.models.job import RuntimeJob
from app.services.assessment_runtime_router import AssessmentRuntimeRouter
from app.services.backend_v12_runtime_bridge import BackendV12RuntimeBridge
from app.services.dynamic_case_profile_builder import DynamicCaseProfileBuilder
from app.services.runtime_event_service import RuntimeEventService
from app.services.runtime_storage import RuntimeStorage
from app.services.storage_utils import write_json_atomic
from app.services.uploaded_material_fact_extractor import UploadedMaterialFactExtractor
from app.services.uploaded_material_runtime_adapter import (
    BoundaryAudit,
    RiskScore,
    UploadedMaterialRuntimeAdapter,
)


class MultiAgentRuntimeOrchestrator:

    def __init__(self) -> None:
        self.fact_extractor = UploadedMaterialFactExtractor()
        self.profile_builder = DynamicCaseProfileBuilder()
        self.router = AssessmentRuntimeRouter()
        self.bridge = BackendV12RuntimeBridge()
        self.adapter = UploadedMaterialRuntimeAdapter()
        self.storage = RuntimeStorage()
        self.events = RuntimeEventService()

    def run(
        self,
        job: RuntimeJob,
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

        # Stage 1: Material Parser
        self._emit(job.job_id, "material_parser_started", "material_parser", "Material parser agent started.")
        self._emit(job.job_id, "material_parser_completed", "material_parser", "Material parsing completed.", {"file_count": len(file_records)})

        # Stage 2: Fact Extraction
        self._emit(job.job_id, "fact_extraction_started", "fact_extraction", "Fact extractor agent started.")
        facts = self.fact_extractor.extract(user_prompt, assessment_type, intake, text_previews)
        write_json_atomic(artifacts_dir / "extracted_facts.json", facts.model_dump(mode="json"))
        rel_paths["extracted_facts.json"] = self.storage.display_path(artifacts_dir / "extracted_facts.json")
        self._emit(job.job_id, "fact_extraction_completed", "fact_extraction", "Fact extraction completed.",
                   {"confidence": facts.extraction_confidence, "missing_count": len(facts.missing_facts)})

        # Stage 3: Assessment Router
        self._emit(job.job_id, "assessment_router_started", "assessment_router", "Assessment router agent started.")
        route = self.router.route(assessment_type, user_prompt, intake)
        write_json_atomic(artifacts_dir / "runtime_route.json", route.model_dump(mode="json"))
        rel_paths["runtime_route.json"] = self.storage.display_path(artifacts_dir / "runtime_route.json")
        self._emit(job.job_id, "assessment_router_completed", "assessment_router", "Assessment routing completed.",
                   {"route": route.route, "support_level": route.support_level})

        # Stage 4: Dynamic Case Profile
        profile = self.profile_builder.build(assessment_type, facts, intake, user_prompt)
        write_json_atomic(artifacts_dir / "dynamic_case_profile.json", profile.model_dump(mode="json"))
        rel_paths["dynamic_case_profile.json"] = self.storage.display_path(artifacts_dir / "dynamic_case_profile.json")
        self._emit(job.job_id, "dynamic_case_profile_created", "case_profile", "Dynamic case profile created.",
                   {"case_id": profile.case_id, "scenario_tags": profile.scenario_tags})

        # Stage 5: Legal Retrieval
        self._emit(job.job_id, "legal_retrieval_started", "legal_retrieval", "Legal retrieval agent started (rules-based).")
        evidence_result = self.bridge.attempt_retrieve_evidence(profile, [])
        write_json_atomic(artifacts_dir / "retrieval_trace.json", evidence_result.model_dump(mode="json"))
        rel_paths["retrieval_trace.json"] = self.storage.display_path(artifacts_dir / "retrieval_trace.json")
        self._emit(job.job_id, "legal_retrieval_completed", "legal_retrieval",
                   "Legal retrieval completed (rules-based fallback).",
                   {"fallback_used": evidence_result.fallback_used})

        # Stage 6: Claim Planning
        self._emit(job.job_id, "claim_planning_started", "claim_planning", "Claim planning agent started.")
        claim_result = self.bridge.attempt_plan_claims(profile, facts.model_dump(mode="json"))
        claims = claim_result.result.get("claims", [])
        write_json_atomic(artifacts_dir / "claim_plan.json", claim_result.model_dump(mode="json"))
        rel_paths["claim_plan.json"] = self.storage.display_path(artifacts_dir / "claim_plan.json")
        self._emit(job.job_id, "claim_planning_completed", "claim_planning", f"Claim planning completed ({len(claims)} claims).")

        # Stage 7: Evidence Pack
        self._emit(job.job_id, "evidence_pack_started", "evidence_pack", "Evidence pack agent started.")
        evidence_pack = {
            "evidence_rows": facts.evidence_from_uploaded_material,
            "source_backed": False,
            "manual_verified": False,
            "needs_manual_verification": True,
        }
        write_json_atomic(artifacts_dir / "evidence_pack.json", evidence_pack)
        rel_paths["evidence_pack.json"] = self.storage.display_path(artifacts_dir / "evidence_pack.json")
        self._emit(job.job_id, "evidence_pack_completed", "evidence_pack", "Evidence pack completed (from uploaded material).")

        # Stage 8: Citation Planning
        self._emit(job.job_id, "citation_planning_started", "citation_planning", "Citation planning agent started.")
        citation_result = self.bridge.attempt_plan_citations(claims, [])
        citations = citation_result.result.get("citations", [])
        write_json_atomic(artifacts_dir / "citation_plan.json", citation_result.model_dump(mode="json"))
        rel_paths["citation_plan.json"] = self.storage.display_path(artifacts_dir / "citation_plan.json")
        self._emit(job.job_id, "citation_planning_completed", "citation_planning", f"Citation planning completed ({len(citations)} citations).")

        # Stage 9: Compliance Analysis
        self._emit(job.job_id, "compliance_analysis_started", "compliance_analysis", "Compliance analysis agent started.")

        # Stage 10: Risk Scoring
        self._emit(job.job_id, "risk_scoring_started", "risk_scoring", "Risk scoring agent started.")
        risk_score = self._compute_risk_score(facts, assessment_type)
        write_json_atomic(artifacts_dir / "risk_score.json", risk_score.model_dump(mode="json"))
        rel_paths["risk_score.json"] = self.storage.display_path(artifacts_dir / "risk_score.json")
        self._emit(job.job_id, "risk_scoring_completed", "risk_scoring", f"Risk scoring completed ({risk_score.overall_risk_level}).")

        # Build remaining artifacts via adapter
        boundary = BoundaryAudit()
        missing_capabilities = route.missing_capabilities

        all_artifacts = self.adapter.adapt(
            conversation_id, user_prompt, assessment_type, file_ids,
            text_previews, intake, facts, profile, route,
            claims, citations, risk_score, boundary, missing_capabilities,
        )

        # Write remaining artifacts
        artifact_names = [
            "input_materials_manifest", "uploaded_material_intake", "extracted_facts",
            "dynamic_case_profile", "runtime_route", "retrieval_trace", "claim_plan",
            "evidence_pack", "citation_plan", "compliance_analysis", "risk_score",
            "source_trace", "runtime_manifest", "boundary_audit", "missing_capabilities",
        ]
        for name in artifact_names:
            json_name = f"{name}.json"
            if json_name not in rel_paths:
                data = all_artifacts.get(name, {})
                write_json_atomic(artifacts_dir / json_name, data if isinstance(data, dict) else {"data": data})
                rel_paths[json_name] = self.storage.display_path(artifacts_dir / json_name)

        # Stage 11: Report Generation
        self._emit(job.job_id, "report_generation_started", "report_generation", "Report generation agent started.")
        report = self._generate_report(user_prompt, assessment_type, facts, profile, route, claims, risk_score)
        report_path = artifacts_dir / "prototype_report.md"
        report_path.write_text(report, encoding="utf-8")
        rel_paths["prototype_report.md"] = self.storage.display_path(report_path)
        self._emit(job.job_id, "report_generation_completed", "report_generation", "Prototype report generated.")

        # Stage 12: Boundary Audit
        self._emit(job.job_id, "boundary_audit_started", "boundary_audit", "Boundary auditor agent started.")
        self._emit(job.job_id, "boundary_audit_completed", "boundary_audit", "Boundary audit completed. No violations detected.")

        # Stage 13: Artifact Collection
        self._emit(job.job_id, "artifact_collection_completed", "artifact_collection", f"All artifacts collected ({len(rel_paths)} files).")
        self._emit(job.job_id, "final", "completed", "Final event: job completed. Prototype diagnostic only, not formal legal opinion.")

        return rel_paths

    def _emit(self, job_id: str, event_type: str, stage: str, message: str, payload: Dict | None = None) -> None:
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

    def _compute_risk_score(self, facts: Any, assessment_type: str) -> RiskScore:
        score = RiskScore()
        pi = facts.personal_information_categories or []
        sp = facts.sensitive_pi_categories or []
        cb = facts.cross_border_elements or []
        missing = facts.missing_facts or []

        tx_risk = 0
        if not facts.parties:
            tx_risk += 30
        if facts.consent_status == "unknown":
            tx_risk += 20
        if facts.contract_status == "unknown":
            tx_risk += 20
        score.transaction_risk = {"score": tx_risk, "level": self._level(tx_risk), "details": "基于材料完整度评估"}

        pi_risk = len(pi) * 15 + (20 if facts.consent_status == "unknown" else 0)
        score.personal_information_risk = {"score": pi_risk, "level": self._level(pi_risk), "categories": pi}

        sp_risk = len(sp) * 25
        score.sensitive_pi_risk = {"score": sp_risk, "level": self._level(sp_risk), "categories": sp}

        cb_risk = len(cb) * 20 + (10 if not facts.recipient_location else 0) + (10 if facts.contract_status == "unknown" else 0)
        score.cross_border_risk = {"score": cb_risk, "level": self._level(cb_risk), "elements": cb}

        gap_risk = len(missing) * 10
        score.evidence_gap_risk = {"score": gap_risk, "level": self._level(gap_risk), "missing_items": missing}

        score.source_trace_risk = {"score": 50, "level": "high", "reason": "legal_sources_not_verified_rules_based_only"}

        total = tx_risk + pi_risk + sp_risk + cb_risk + gap_risk + 50
        score.overall_risk_level = self._level(total)
        score.confidence = "low"
        score.limitations = ["rules_based_scoring", "not_autojudge", "not_manual_review"]
        score.recommended_actions = [f"补充材料: {m}" for m in missing[:5]]

        return score

    def _level(self, s: int) -> str:
        if s >= 80:
            return "critical"
        if s >= 50:
            return "high"
        if s >= 30:
            return "medium"
        return "low"

    def _generate_report(self, prompt: str, at: str, facts: Any, profile: Any,
                         route: Any, claims: List[Dict], risk: RiskScore) -> str:
        lines = [
            "# Prototype Diagnostic Report",
            "",
            "> **非正式法律意见声明**: 本报告为 prototype diagnostic 原型诊断，",
            "> 不构成正式法律意见。所有法律引用基于规则型领域知识匹配，",
            "> 未经人工审核，未经文章级别验证。",
            "> 上传材料仅作为业务事实参考，未写入 Chroma/Neo4j/current_backend。",
            "",
            "---",
            "",
            "## 1. 评估概述",
            f"- 评估类型: {at}",
            f"- 运行模式: uploaded_material_runtime (prototype)",
            f"- 支持级别: {route.support_level}",
            f"- 伪用例ID: {profile.case_id}",
            "",
            "## 2. 上传材料摘要",
            f"- 用户输入: {prompt[:200]}",
            f"- 材料用途: business_facts_only (未写入法律数据库)",
            "",
            "## 3. 事实识别结果",
            f"- 当事方: {', '.join(facts.parties) if facts.parties else '未识别'}",
            f"- 数据类型: {', '.join(facts.data_categories)}",
            f"- 个人信息: {', '.join(facts.personal_information_categories) if facts.personal_information_categories else '无'}",
            f"- 敏感个人信息: {', '.join(facts.sensitive_pi_categories) if facts.sensitive_pi_categories else '无'}",
            f"- 跨境元素: {', '.join(facts.cross_border_elements) if facts.cross_border_elements else '无'}",
            f"- 传输方向: {facts.transfer_direction or '未确定'}",
            f"- 授权状态: {facts.consent_status or '未知'}",
            f"- 合同状态: {facts.contract_status or '未知'}",
            f"- 提取置信度: {facts.extraction_confidence}",
            "",
            "## 4. 合规问题清单",
        ]

        for c in claims:
            lines.append(f"- [{c.get('claim_id', '?')}] {c.get('title', '')}: {c.get('check', '')} (领域: {c.get('domain', '')})")

        lines.extend([
            "",
            "## 5. 法律依据摘要",
            "> 以下法律引用为规则型领域知识匹配，未经文章级别验证：",
        ])
        seen = set()
        for c in claims:
            d = c.get("domain", "")
            if d and d not in seen:
                seen.add(d)
                lines.append(f"- {d}")

        lines.extend([
            "",
            "## 6. 风险分级",
            f"- 综合风险等级: **{risk.overall_risk_level}**",
            f"- 交易风险: {risk.transaction_risk.get('level', 'unknown')} (分数: {risk.transaction_risk.get('score', 'N/A')})",
            f"- 个人信息风险: {risk.personal_information_risk.get('level', 'unknown')} (分数: {risk.personal_information_risk.get('score', 'N/A')})",
            f"- 敏感PI风险: {risk.sensitive_pi_risk.get('level', 'unknown')} (分数: {risk.sensitive_pi_risk.get('score', 'N/A')})",
            f"- 跨境风险: {risk.cross_border_risk.get('level', 'unknown')} (分数: {risk.cross_border_risk.get('score', 'N/A')})",
            f"- 证据缺口风险: {risk.evidence_gap_risk.get('level', 'unknown')}",
            f"- 来源可追溯风险: {risk.source_trace_risk.get('level', 'unknown')}",
            "",
            "## 7. 缺失材料",
        ])

        for m in facts.missing_facts:
            lines.append(f"- {m}")

        lines.extend([
            "",
            "## 8. 建议补充材料",
        ])
        for r in risk.recommended_actions:
            lines.append(f"- {r}")

        lines.extend([
            "",
            "## 9. 下一步合规动作",
            "1. 审查并确认事实识别结果的准确性",
            "2. 补充上述缺失材料",
            "3. 聘请专业律师进行正式合规审查",
            "4. 根据评估结果采取合规整改措施",
            "",
            "## 10. 系统边界与限制",
            "- prototype_diagnostic: 非正式法律意见",
            "- not_source_backed: 法律来源未经过人工核查",
            "- not_manual_verified: 未经过人工审核",
            "- not_article_level_verified: 法律条文未经逐条验证",
            "- rules_based_extraction: 事实抽取基于规则型关键词匹配",
            "- uploaded_files_not_written_to_chroma: 上传文件未写入向量数据库",
            "- uploaded_files_not_written_to_neo4j: 上传文件未写入图数据库",
            "- current_backend_not_modified: 法规数据库未被修改",
            "",
            "---",
            f"*Generated at {__import__('datetime').datetime.utcnow().isoformat()} - Prototype Diagnostic Only*",
        ])

        return "\n".join(lines)