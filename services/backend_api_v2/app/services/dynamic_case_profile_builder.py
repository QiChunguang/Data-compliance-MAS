from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.services.uploaded_material_fact_extractor import ExtractedFacts


class DynamicCaseProfile(BaseModel):
    case_id: str
    case_origin: str = "uploaded_material_runtime"
    assessment_type: str
    facts: Dict[str, Any] = Field(default_factory=dict)
    scenario_tags: List[str] = Field(default_factory=list)
    legal_domains: List[str] = Field(default_factory=list)
    expected_retrieval_groups: List[str] = Field(default_factory=list)
    claim_plan_hints: List[str] = Field(default_factory=list)
    risk_dimensions: List[str] = Field(default_factory=list)
    report_sections: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    uploaded_material_trace: List[str] = Field(default_factory=list)


class DynamicCaseProfileBuilder:

    def build(
        self,
        assessment_type: str,
        facts: ExtractedFacts,
        intake: Any,
        user_prompt: str,
    ) -> DynamicCaseProfile:
        pseudo = self._map_pseudo_case_id(assessment_type, facts)
        scenario_tags = self._derive_scenario_tags(assessment_type, facts)
        legal_domains = self._derive_legal_domains(assessment_type, facts)
        retrieval_groups = self._derive_retrieval_groups(assessment_type, facts)
        claim_hints = self._derive_claim_hints(assessment_type, facts)
        risk_dims = self._derive_risk_dimensions(assessment_type, facts)
        report_sections = self._derive_report_sections(assessment_type)
        limitations = self._derive_limitations(facts)
        trace = self._build_material_trace(facts, intake)

        return DynamicCaseProfile(
            case_id=pseudo,
            case_origin="uploaded_material_runtime",
            assessment_type=assessment_type,
            facts=facts.model_dump(mode="json"),
            scenario_tags=scenario_tags,
            legal_domains=legal_domains,
            expected_retrieval_groups=retrieval_groups,
            claim_plan_hints=claim_hints,
            risk_dimensions=risk_dims,
            report_sections=report_sections,
            limitations=limitations,
            uploaded_material_trace=trace,
        )

    def _map_pseudo_case_id(self, at: str, facts: ExtractedFacts) -> str:
        cross = bool(facts.cross_border_elements)
        pi = bool(facts.personal_information_categories)
        sp = bool(facts.sensitive_pi_categories)
        if at == "data_transaction_compliance":
            if pi and cross:
                return "uploaded_dynamic_data_transaction_cross_border_pi"
            if pi:
                return "uploaded_dynamic_data_transaction_pi"
            return "uploaded_dynamic_data_transaction"
        if at == "cross_border_data_transfer":
            if pi and sp:
                return "uploaded_dynamic_cross_border_sensitive_pi"
            if pi:
                return "uploaded_dynamic_cross_border_pi"
            return "uploaded_dynamic_cross_border"
        if at == "pipl_personal_information_protection":
            return "uploaded_dynamic_pipl"
        if at == "data_flow_security_review":
            return "uploaded_dynamic_data_flow_security"
        return "uploaded_dynamic_general"

    def _derive_scenario_tags(self, at: str, facts: ExtractedFacts) -> List[str]:
        tags: List[str] = []
        if at == "data_transaction_compliance":
            tags.append("data_transaction")
        if at == "cross_border_data_transfer":
            tags.append("cross_border_transfer")
        if facts.cross_border_elements:
            tags.append("cross_border")
        if facts.personal_information_categories:
            tags.append("personal_information_involved")
        if facts.sensitive_pi_categories:
            tags.append("sensitive_pi_involved")
        if facts.important_data_indicators:
            tags.append("potential_important_data")
        return tags

    def _derive_legal_domains(self, at: str, facts: ExtractedFacts) -> List[str]:
        domains = ["网络安全法", "数据安全法"]
        if facts.personal_information_categories or at in ("pipl_personal_information_protection",):
            domains.append("个人信息保护法")
        if at == "data_transaction_compliance":
            domains.extend(["数据交易相关法规", "数据二十条"])
        if facts.cross_border_elements or at == "cross_border_data_transfer":
            domains.extend(["数据出境安全评估办法", "促进和规范数据跨境流动规定", "个人信息出境标准合同办法"])
        return list(dict.fromkeys(domains))

    def _derive_retrieval_groups(self, at: str, facts: ExtractedFacts) -> List[str]:
        groups = ["data_security_basics"]
        if at in ("data_transaction_compliance",) or "交易" in str(facts.transaction_type):
            groups.append("data_transaction_rules")
        if facts.cross_border_elements or at == "cross_border_data_transfer":
            groups.append("cross_border_transfer_rules")
        if facts.personal_information_categories:
            groups.append("personal_information_protection")
        if facts.sensitive_pi_categories:
            groups.append("sensitive_pi_rules")
        return groups

    def _derive_claim_hints(self, at: str, facts: ExtractedFacts) -> List[str]:
        hints: List[str] = []
        if facts.personal_information_categories:
            hints.append("需要确认个人信息处理的合法性基础")
            if facts.consent_status == "unknown":
                hints.append("需要核查是否取得用户授权同意")
        if facts.cross_border_elements or at == "cross_border_data_transfer":
            hints.append("需要确认是否满足数据出境条件")
            hints.append("需要核查是否完成安全评估/标准合同备案/认证")
        if at == "data_transaction_compliance":
            hints.append("需要核查数据来源合法性")
            hints.append("需要核查数据权属和授权链条")
        if facts.sensitive_pi_categories:
            hints.append("需要核查敏感个人信息处理的单独同意")
        return hints

    def _derive_risk_dimensions(self, at: str, facts: ExtractedFacts) -> List[str]:
        dims = ["compliance_baseline"]
        if facts.personal_information_categories:
            dims.append("personal_information_risk")
        if facts.sensitive_pi_categories:
            dims.append("sensitive_pi_risk")
        if facts.cross_border_elements or at == "cross_border_data_transfer":
            dims.append("cross_border_risk")
        if at == "data_transaction_compliance":
            dims.append("transaction_risk")
        dims.append("evidence_gap_risk")
        return dims

    def _derive_report_sections(self, at: str) -> List[str]:
        sections = [
            "1. 评估概述",
            "2. 上传材料摘要",
            "3. 事实识别结果",
            "4. 合规问题分析",
            "5. 法律依据",
        ]
        if at == "data_transaction_compliance":
            sections.extend([
                "6.1 交易主体合规",
                "6.2 数据来源合法性",
                "6.3 数据权属与授权",
                "6.4 个人信息保护",
                "6.5 合同条款审查",
                "6.6 安全措施评估",
            ])
        elif at == "cross_border_data_transfer":
            sections.extend([
                "6.1 出境场景识别",
                "6.2 数据类型与分类",
                "6.3 出境路径分析",
                "6.4 接收方评估",
                "6.5 安全评估/标准合同/认证",
            ])
        sections.extend([
            "7. 风险分级",
            "8. 缺失材料",
            "9. 建议补充材料",
            "10. 下一步合规动作",
            "11. 系统边界与限制",
        ])
        return sections

    def _derive_limitations(self, facts: ExtractedFacts) -> List[str]:
        lims = [
            "prototype_diagnostic: 非正式法律意见",
            "not_source_backed: 法律来源为规则型匹配，非人工核查",
            "not_manual_verified: 未经过人工审核",
            "uploaded_material_as_business_facts_only: 上传材料仅作为业务事实参考",
        ]
        if facts.extraction_confidence == "low":
            lims.append("low_confidence_extraction: 事实抽取置信度低，建议补充更多材料")
        return lims

    def _build_material_trace(self, facts: ExtractedFacts, intake: Any) -> List[str]:
        trace: List[str] = []
        file_count = getattr(intake, "file_count", 0) or 0
        trace.append(f"uploaded_files_count: {file_count}")
        trace.append(f"extraction_confidence: {facts.extraction_confidence}")
        trace.append("uploaded_files_not_written_to_chroma_or_neo4j: true")
        return trace