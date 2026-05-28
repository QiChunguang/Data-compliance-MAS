from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RuntimeRoute(BaseModel):
    assessment_type: str
    route: str
    support_level: str
    selected_agents: List[str] = Field(default_factory=list)
    selected_legal_domains: List[str] = Field(default_factory=list)
    selected_retrieval_strategy: str = "rules_based"
    missing_capabilities: List[str] = Field(default_factory=list)


class AssessmentRuntimeRouter:

    def route(self, assessment_type: str, user_prompt: str, intake: Any) -> RuntimeRoute:
        cross_border_detected = self._detect_cross_border(user_prompt, intake)
        effective_type = assessment_type
        if cross_border_detected and assessment_type not in ("cross_border_data_transfer",):
            effective_type = "cross_border_data_transfer"

        if effective_type == "data_transaction_compliance":
            return RuntimeRoute(
                assessment_type=effective_type,
                route="data_transaction",
                support_level="full_prototype",
                selected_agents=self._agents_for_data_transaction(),
                selected_legal_domains=["网络安全法", "数据安全法", "个人信息保护法", "数据交易相关法规"],
                selected_retrieval_strategy="rules_based_with_intake",
                missing_capabilities=[],
            )
        if effective_type == "cross_border_data_transfer":
            return RuntimeRoute(
                assessment_type=effective_type,
                route="cross_border",
                support_level="full_prototype",
                selected_agents=self._agents_for_cross_border(),
                selected_legal_domains=[
                    "网络安全法", "数据安全法", "个人信息保护法",
                    "数据出境安全评估办法", "促进和规范数据跨境流动规定",
                    "个人信息出境标准合同办法",
                ],
                selected_retrieval_strategy="rules_based_with_intake",
                missing_capabilities=[],
            )
        if effective_type == "pipl_personal_information_protection":
            return RuntimeRoute(
                assessment_type=effective_type,
                route="pipl_limited",
                support_level="limited_prototype",
                selected_agents=self._agents_for_pipl(),
                selected_legal_domains=["个人信息保护法", "网络安全法"],
                selected_retrieval_strategy="rules_based",
                missing_capabilities=["完整PIPL条文逐条匹配需RAG增强"],
            )
        if effective_type == "data_flow_security_review":
            return RuntimeRoute(
                assessment_type=effective_type,
                route="data_flow_limited",
                support_level="limited_prototype",
                selected_agents=self._agents_for_data_flow(),
                selected_legal_domains=["数据安全法", "网络安全法"],
                selected_retrieval_strategy="rules_based",
                missing_capabilities=["数据流拓扑分析需额外材料"],
            )
        return RuntimeRoute(
            assessment_type=effective_type,
            route="general_limited",
            support_level="unsupported",
            selected_agents=[],
            selected_legal_domains=["网络安全法", "数据安全法"],
            selected_retrieval_strategy="rules_based",
            missing_capabilities=["不支持该评估类型的完整运行时"],
        )

    def _detect_cross_border(self, prompt: str, intake: Any) -> bool:
        keywords = ["出境", "跨境", "境外", "海外", "跨国", "境外接收方", "数据出海", "overseas"]
        if any(kw in prompt for kw in keywords):
            return True
        intake_cb = getattr(intake, "cross_border_indicators", []) or []
        return len(intake_cb) > 0

    def _agents_for_data_transaction(self) -> List[str]:
        return [
            "material_parser_agent",
            "fact_extraction_agent",
            "assessment_router_agent",
            "legal_retrieval_agent",
            "claim_planning_agent",
            "evidence_pack_agent",
            "citation_planning_agent",
            "compliance_analysis_agent",
            "risk_scoring_agent",
            "report_generation_agent",
            "boundary_auditor_agent",
        ]

    def _agents_for_cross_border(self) -> List[str]:
        return [
            "material_parser_agent",
            "fact_extraction_agent",
            "assessment_router_agent",
            "legal_retrieval_agent",
            "claim_planning_agent",
            "evidence_pack_agent",
            "citation_planning_agent",
            "compliance_analysis_agent",
            "risk_scoring_agent",
            "report_generation_agent",
            "boundary_auditor_agent",
        ]

    def _agents_for_pipl(self) -> List[str]:
        return [
            "material_parser_agent",
            "fact_extraction_agent",
            "compliance_analysis_agent",
            "report_generation_agent",
            "boundary_auditor_agent",
        ]

    def _agents_for_data_flow(self) -> List[str]:
        return [
            "material_parser_agent",
            "fact_extraction_agent",
            "compliance_analysis_agent",
            "report_generation_agent",
            "boundary_auditor_agent",
        ]