from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.services.uploaded_material_fact_extractor import ExtractedFacts


class RiskScore(BaseModel):
    overall_risk_level: str = "unknown"
    transaction_risk: Dict[str, Any] = Field(default_factory=dict)
    personal_information_risk: Dict[str, Any] = Field(default_factory=dict)
    sensitive_pi_risk: Dict[str, Any] = Field(default_factory=dict)
    cross_border_risk: Dict[str, Any] = Field(default_factory=dict)
    evidence_gap_risk: Dict[str, Any] = Field(default_factory=dict)
    source_trace_risk: Dict[str, Any] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    confidence: str = "low"
    limitations: List[str] = Field(default_factory=list)


class BoundaryAudit(BaseModel):
    formal_legal_opinion: bool = False
    prototype_diagnostic: bool = True
    uploaded_files_written_to_chroma: bool = False
    uploaded_files_written_to_neo4j: bool = False
    uploaded_files_written_to_legal_data: bool = False
    current_backend_modified: bool = False
    chroma_modified: bool = False
    neo4j_modified: bool = False
    autojudge_scoring_modified: bool = False
    autojudge_scoring_schema_modified: bool = False
    cap_rules_modified: bool = False
    legal_data_modified: bool = False
    source_backed_claim_fabricated: bool = False
    manual_verified_claim_fabricated: bool = False
    article_level_verified_claim_fabricated: bool = False
    legal_sources_from_rag_only: bool = True
    uploaded_material_used_as_business_facts_only: bool = True


class UploadedMaterialRuntimeAdapter:

    def adapt(
        self,
        conversation_id: str,
        user_prompt: str,
        assessment_type: str,
        file_ids: List[str],
        text_previews: List[str],
        intake: Any,
        facts: ExtractedFacts,
        profile: Any,
        route: Any,
        claims: List[Dict],
        citations: List[Dict],
        risk_score: RiskScore,
        boundary: BoundaryAudit,
        missing_capabilities: List[str],
    ) -> Dict[str, Any]:
        return {
            "input_materials_manifest": {
                "conversation_id": conversation_id,
                "user_prompt": user_prompt,
                "assessment_type": assessment_type,
                "file_ids": file_ids,
                "uploaded_material_usage": "business_facts_only_dynamic_runtime_prototype",
                "files_not_written_to_chroma": True,
                "files_not_written_to_neo4j": True,
            },
            "uploaded_material_intake": intake.model_dump(mode="json") if hasattr(intake, "model_dump") else intake,
            "extracted_facts": facts.model_dump(mode="json"),
            "dynamic_case_profile": profile.model_dump(mode="json"),
            "runtime_route": route.model_dump(mode="json"),
            "retrieval_trace": {
                "retrieval_source": "rules_based_prototype",
                "rag_query_attempted": False,
                "rag_query_reason": "core_v12_retrieval_not_safe_for_dynamic_facts",
                "law_references": [c.get("law", "") for c in citations],
                "article_level_verified": False,
            },
            "claim_plan": {"claims": claims, "total_claims": len(claims)},
            "evidence_pack": {
                "evidence_rows": [],
                "source_backed": False,
                "manual_verified": False,
                "article_level_verified": False,
                "needs_manual_verification": True,
                "note": "evidence_from_uploaded_material_only_not_legal_database",
            },
            "citation_plan": {"citations": citations, "diagnostic_only": True},
            "compliance_analysis": self._build_compliance_analysis(assessment_type, facts, claims),
            "risk_score": risk_score.model_dump(mode="json"),
            "source_trace": {
                "evidence_sources": facts.evidence_from_uploaded_material,
                "source_backed": False,
                "source_trace_caveat": "not_manual_verification",
                "all_from_uploaded_materials": True,
                "no_legal_database_source": True,
            },
            "runtime_manifest": self._build_runtime_manifest(route),
            "boundary_audit": boundary.model_dump(mode="json"),
            "missing_capabilities": {
                "status": "limited" if missing_capabilities else "complete_for_prototype",
                "missing": missing_capabilities,
                "next_fixes": [
                    "接入RAG检索以获取真实法条匹配",
                    "接入Chroma/legal_data以获取精确法律依据",
                    "人工审核以提升source_backed和manual_verified等级",
                ],
            },
        }

    def _build_compliance_analysis(self, at: str, facts: ExtractedFacts, claims: List[Dict]) -> Dict[str, Any]:
        findings: List[str] = []
        recommendations: List[str] = []

        if at == "data_transaction_compliance":
            findings.extend(["需要核实数据交易主体的合规资质", "需要核查数据来源的合法性", "需要确认数据权属和授权链条"])
            recommendations.extend(["建议提供交易合同或协议文本", "建议提供数据来源的证明材料", "建议提供数据授权/同意的相关文件"])

        elif at == "cross_border_data_transfer":
            findings.extend(["需要明确数据出境的具体场景", "需要确认适用的出境路径", "需要评估境外接收方的数据保护能力"])
            recommendations.extend(["建议提供数据出境的具体业务场景说明", "建议提供境外接收方的数据保护措施信息", "建议确认是否已签署标准合同或完成安全评估"])

        if facts.personal_information_categories:
            findings.append("涉及个人信息处理，需要确认合法性基础")
            if facts.consent_status == "unknown":
                recommendations.append("建议提供用户告知同意的相关证明")

        if facts.sensitive_pi_categories:
            findings.append("涉及敏感个人信息，合规要求更为严格")
            recommendations.append("建议确认是否已取得用户的单独同意")

        if facts.missing_facts:
            for m in facts.missing_facts:
                recommendations.append(f"补充材料: {m}")

        return {
            "assessment_type": at,
            "findings": findings,
            "recommendations": recommendations,
            "not_formal_legal_opinion": True,
        }

    def _build_runtime_manifest(self, route: Any) -> Dict[str, Any]:
        stages = [
            {"stage": "material_parser", "agent": "material_parser_agent", "status": "completed"},
            {"stage": "fact_extraction", "agent": "fact_extraction_agent", "status": "completed"},
            {"stage": "assessment_routing", "agent": "assessment_router_agent", "status": "completed"},
            {"stage": "legal_retrieval", "agent": "legal_retrieval_agent", "status": "completed_fallback"},
            {"stage": "claim_planning", "agent": "claim_planning_agent", "status": "completed"},
            {"stage": "evidence_pack", "agent": "evidence_pack_agent", "status": "completed_fallback"},
            {"stage": "citation_planning", "agent": "citation_planning_agent", "status": "completed"},
            {"stage": "compliance_analysis", "agent": "compliance_analysis_agent", "status": "completed"},
            {"stage": "risk_scoring", "agent": "risk_scoring_agent", "status": "completed"},
            {"stage": "report_generation", "agent": "report_generation_agent", "status": "completed"},
            {"stage": "boundary_audit", "agent": "boundary_auditor_agent", "status": "completed"},
        ]
        return {
            "runtime_mode": "uploaded_material_runtime",
            "support_level": getattr(route, "support_level", "unknown"),
            "stages": stages,
            "source_backed": False,
            "manual_verified": False,
            "formal_legal_opinion": False,
        }
