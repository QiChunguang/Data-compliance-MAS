from __future__ import annotations

import sys
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.core.config import get_settings


class V12BridgeResult(BaseModel):
    module: str
    status: str
    result: Dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None


class BackendV12RuntimeBridge:
    """Read-only bridge to core/v12. Falls back when core/v12 cannot be safely called."""

    def __init__(self) -> None:
        self._core_available = False
        self._core_error: str | None = None

    def attempt_normalize_facts(self, case_id: str, facts: Dict[str, Any]) -> V12BridgeResult:
        return V12BridgeResult(
            module="fact_normalizer",
            status="fallback",
            result={"normalized_facts": facts},
            fallback_used=True,
            fallback_reason="core/v12 fact_normalizer requires registered case contract; using raw facts",
        )

    def attempt_plan_claims(self, profile: Any, facts: Dict[str, Any]) -> V12BridgeResult:
        claims = self._generate_rules_claims(profile, facts)
        return V12BridgeResult(
            module="claim_planner",
            status="fallback",
            result={"claims": claims},
            fallback_used=True,
            fallback_reason="core/v12 claim_planner requires registered case profile; using rules-based claims",
        )

    def attempt_retrieve_evidence(self, profile: Any, claims: List[Dict]) -> V12BridgeResult:
        return V12BridgeResult(
            module="primary_evidence_retriever",
            status="fallback",
            result={"evidence_rows": [], "retrieval_source": "rules_based_prototype"},
            fallback_used=True,
            fallback_reason="core/v12 evidence retriever requires preset case_id for Chroma/legal_data retrieval",
        )

    def attempt_build_evidence_pack(self, claims: List[Dict], evidence: List[Dict]) -> V12BridgeResult:
        return V12BridgeResult(
            module="evidence_pack_builder",
            status="fallback",
            result={"evidence_pack": [], "source_backed": False},
            fallback_used=True,
            fallback_reason="evidence_pack built from rules-based claims, not real retrieval",
        )

    def attempt_plan_citations(self, claims: List[Dict], evidence: List[Dict]) -> V12BridgeResult:
        return V12BridgeResult(
            module="citation_planner",
            status="fallback",
            result={"citations": self._generate_rules_citations(claims)},
            fallback_used=True,
            fallback_reason="citations generated from domain knowledge, not article-level verification",
        )

    def attempt_render_report(self, profile: Any, claims: List[Dict], evidence: List[Dict],
                              citations: List[Dict], risk: Dict) -> V12BridgeResult:
        return V12BridgeResult(
            module="report_renderer",
            status="fallback",
            result={"rendered_report": None},
            fallback_used=True,
            fallback_reason="using backend report renderer instead of core/v12",
        )

    def _generate_rules_claims(self, profile: Any, facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        claims: List[Dict[str, Any]] = []
        at = getattr(profile, "assessment_type", "")

        if at == "data_transaction_compliance":
            claims.extend([
                {"claim_id": "DT-001", "title": "交易主体合规", "domain": "网络安全法", "check": "交易主体是否具备合法经营资质"},
                {"claim_id": "DT-002", "title": "数据来源合法性", "domain": "数据安全法", "check": "数据来源是否合法"},
                {"claim_id": "DT-003", "title": "数据权属清晰", "domain": "数据安全法", "check": "数据权属是否清晰明确"},
            ])
        elif at == "cross_border_data_transfer":
            claims.extend([
                {"claim_id": "CB-001", "title": "出境场景识别", "domain": "数据出境安全评估办法", "check": "是否构成数据出境"},
                {"claim_id": "CB-002", "title": "出境路径合规", "domain": "数据出境安全评估办法", "check": "是否满足安全评估/标准合同/认证条件"},
                {"claim_id": "CB-003", "title": "接收方评估", "domain": "个人信息出境标准合同办法", "check": "境外接收方数据保护能力"},
            ])

        pi = facts.get("personal_information_categories", [])
        if pi:
            claims.append({"claim_id": "PI-001", "title": "个人信息处理合法性基础", "domain": "个人信息保护法", "check": "处理个人信息是否具备合法性基础"})
            claims.append({"claim_id": "PI-002", "title": "告知同意义务", "domain": "个人信息保护法", "check": "是否履行告知和取得同意义务"})

        sp = facts.get("sensitive_pi_categories", [])
        if sp:
            claims.append({"claim_id": "SP-001", "title": "敏感个人信息单独同意", "domain": "个人信息保护法", "check": "处理敏感个人信息是否取得单独同意"})

        cb = facts.get("cross_border_elements", [])
        if cb:
            claims.append({"claim_id": "CB-004", "title": "个人信息出境告知", "domain": "个人信息保护法", "check": "个人信息出境是否履行告知义务"})

        return claims

    def _generate_rules_citations(self, claims: List[Dict]) -> List[Dict[str, Any]]:
        law_map = {
            "网络安全法": ("中华人民共和国网络安全法", "2017-06-01"),
            "数据安全法": ("中华人民共和国数据安全法", "2021-09-01"),
            "个人信息保护法": ("中华人民共和国个人信息保护法", "2021-11-01"),
            "数据出境安全评估办法": ("数据出境安全评估办法", "2022-09-01"),
            "个人信息出境标准合同办法": ("个人信息出境标准合同办法", "2023-06-01"),
            "促进和规范数据跨境流动规定": ("促进和规范数据跨境流动规定", "2024-03-22"),
        }
        citations: List[Dict[str, Any]] = []
        seen = set()
        for claim in claims:
            domain = claim.get("domain", "")
            if domain in law_map and domain not in seen:
                seen.add(domain)
                law_name, effective_date = law_map[domain]
                citations.append({
                    "claim_id": claim.get("claim_id"),
                    "law": law_name,
                    "effective_date": effective_date,
                    "article_specific": False,
                    "article_level_verified": False,
                    "note": "rules_based_reference_only_not_article_verified",
                })
        return citations