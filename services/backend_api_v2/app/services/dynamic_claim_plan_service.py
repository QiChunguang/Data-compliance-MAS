from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ClaimItem(BaseModel):
    claim_id: str = ""
    title: str = ""
    check: str = ""
    domain: str = ""
    law: str = ""
    fact_refs: List[str] = Field(default_factory=list)
    claim_type: str = "legal_basis"
    support_status: str = "unsupported"
    needs_manual_verification: bool = True


class ClaimPlanResult(BaseModel):
    assessment_type: str = ""
    total_claims: int = 0
    claims: List[ClaimItem] = Field(default_factory=list)
    fallback_used: bool = True
    source: str = "rules_based"


class DynamicClaimPlanService:
    def build(self, assessment_type: str, facts: Dict[str, Any],
              retrieval_trace: Any = None) -> ClaimPlanResult:
        claims = self._generate_claims(assessment_type, facts)
        return ClaimPlanResult(
            assessment_type=assessment_type,
            total_claims=len(claims),
            claims=claims,
            fallback_used=False,
            source="dynamic_claim_plan_service",
        )

    def build_from_bridge(self, bridge_claims: List[Any]) -> ClaimPlanResult:
        claims = []
        for c in bridge_claims:
            cd = c.__dict__ if hasattr(c, '__dict__') else c
            if isinstance(cd, dict):
                claims.append(ClaimItem(
                    claim_id=cd.get("claim_id", ""),
                    title=cd.get("claim_text", ""),
                    check=cd.get("claim_text", ""),
                    domain=cd.get("claim_type", "legal_basis"),
                    law="",
                    fact_refs=cd.get("fact_refs", []),
                    claim_type=cd.get("claim_type", "legal_basis"),
                    support_status=cd.get("support_status", "unsupported"),
                ))
        return ClaimPlanResult(
            assessment_type="bridge",
            total_claims=len(claims),
            claims=claims,
            fallback_used=False,
            source="core_v12_bridge",
        )

    def _generate_claims(self, assessment_type: str, facts: Dict[str, Any]) -> List[ClaimItem]:
        claims: List[ClaimItem] = []
        idx = 1

        if "data_transaction" in assessment_type:
            claims.extend([
                ClaimItem(claim_id=f"DT-{idx:02d}", title="数据来源合法性",
                         check="核查数据来源是否合法，确认数据获取方式是否符合法律规定",
                         domain="数据交易合规", law="数据安全法",
                         claim_type="legal_basis", fact_refs=["data_provider", "consent_status"]),
                ClaimItem(claim_id=f"DT-{idx+1:02d}", title="数据权属与授权",
                         check="确认数据权属清晰、授权链条完整",
                         domain="数据交易合规", law="数据安全法",
                         claim_type="legal_basis", fact_refs=["parties", "consent_status"]),
                ClaimItem(claim_id=f"DT-{idx+2:02d}", title="交易范围合规",
                         check="核查数据交易范围是否超出授权范围",
                         domain="数据交易合规", law="数据安全法",
                         claim_type="legal_basis", fact_refs=["processing_purpose"]),
                ClaimItem(claim_id=f"DT-{idx+3:02d}", title="个人信息处理合法性",
                         check="确认个人信息处理是否具有合法性基础",
                         domain="个人信息保护", law="个人信息保护法",
                         claim_type="legal_basis", fact_refs=["personal_information_categories", "consent_status"]),
                ClaimItem(claim_id=f"DT-{idx+4:02d}", title="敏感个人信息合规",
                         check="核查敏感个人信息处理是否取得单独同意",
                         domain="个人信息保护", law="个人信息保护法",
                         claim_type="legal_basis", fact_refs=["sensitive_pi_categories", "consent_status"]),
                ClaimItem(claim_id=f"DT-{idx+5:02d}", title="合同条款合规",
                         check="核查数据交易合同是否包含法定必备条款",
                         domain="数据交易合规", law="数据安全法",
                         claim_type="legal_basis", fact_refs=["contract_status"]),
                ClaimItem(claim_id=f"DT-{idx+6:02d}", title="安全保障措施",
                         check="核查数据处理方是否采取了充分的安全保障措施",
                         domain="数据安全", law="数据安全法",
                         claim_type="legal_basis", fact_refs=["security_measures"]),
                ClaimItem(claim_id=f"DT-{idx+7:02d}", title="数据交易平台义务",
                         check="核查数据交易平台是否履行法定合规义务",
                         domain="数据交易合规", law="数据安全法",
                         claim_type="legal_basis", fact_refs=["platform_or_intermediary_role"]),
                ClaimItem(claim_id=f"DT-{idx+8:02d}", title="证据完整性",
                         check="核查是否存在证据缺口，材料是否完整",
                         domain="证据合规", law="通用",
                         claim_type="evidence_gap", fact_refs=["missing_facts"]),
            ])
            idx += 9

        if "cross_border" in assessment_type:
            claims.extend([
                ClaimItem(claim_id=f"CB-{idx:02d}", title="数据出境认定",
                         check="确认是否存在数据出境行为",
                         domain="跨境数据传输", law="数据出境安全评估办法",
                         claim_type="legal_basis", fact_refs=["cross_border_elements", "transfer_direction"]),
                ClaimItem(claim_id=f"CB-{idx+1:02d}", title="境外接收方识别",
                         check="识别境外接收方身份和所在地",
                         domain="跨境数据传输", law="数据出境安全评估办法",
                         claim_type="legal_basis", fact_refs=["data_recipient", "recipient_location"]),
                ClaimItem(claim_id=f"CB-{idx+2:02d}", title="出境数据类型",
                         check="核查出境数据是否涉及个人信息、敏感个人信息或重要数据",
                         domain="跨境数据传输", law="数据安全法",
                         claim_type="legal_basis", fact_refs=["data_categories", "personal_information_categories"]),
                ClaimItem(claim_id=f"CB-{idx+3:02d}", title="出境路径合规",
                         check="核查是否已选择适当的出境路径（安全评估/标准合同/认证）",
                         domain="跨境数据传输", law="数据出境安全评估办法",
                         claim_type="legal_basis", fact_refs=["contract_status"]),
                ClaimItem(claim_id=f"CB-{idx+4:02d}", title="告知同意",
                         check="确认是否已向用户告知数据出境情况并取得同意",
                         domain="个人信息保护", law="个人信息保护法",
                         claim_type="legal_basis", fact_refs=["consent_status"]),
                ClaimItem(claim_id=f"CB-{idx+5:02d}", title="境外接收方保护能力",
                         check="评估境外接收方是否具备充分的数据保护能力",
                         domain="跨境数据传输", law="数据出境安全评估办法",
                         claim_type="legal_basis", fact_refs=["security_measures"]),
                ClaimItem(claim_id=f"CB-{idx+6:02d}", title="后续转移管控",
                         check="核查是否存在向第三方再转移的风险及管控措施",
                         domain="跨境数据传输", law="数据出境安全评估办法",
                         claim_type="legal_basis", fact_refs=["processing_purpose"]),
                ClaimItem(claim_id=f"CB-{idx+7:02d}", title="重要数据风险评估",
                         check="评估出境数据是否包含重要数据及相应风险",
                         domain="数据安全", law="数据安全法",
                         claim_type="legal_basis", fact_refs=["important_data_indicators"]),
                ClaimItem(claim_id=f"CB-{idx+8:02d}", title="证据缺口",
                         check="核查跨境数据传输合规的证据完整性",
                         domain="证据合规", law="通用",
                         claim_type="evidence_gap", fact_refs=["missing_facts"]),
            ])

        return claims