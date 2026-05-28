from __future__ import annotations

import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ExtractedFacts(BaseModel):
    parties: List[str] = Field(default_factory=list)
    data_provider: str | None = None
    data_recipient: str | None = None
    data_subjects: List[str] = Field(default_factory=list)
    data_categories: List[str] = Field(default_factory=list)
    personal_information_categories: List[str] = Field(default_factory=list)
    sensitive_pi_categories: List[str] = Field(default_factory=list)
    transaction_type: str | None = None
    processing_purpose: List[str] = Field(default_factory=list)
    transfer_direction: str | None = None
    cross_border_elements: List[str] = Field(default_factory=list)
    recipient_location: str | None = None
    security_measures: List[str] = Field(default_factory=list)
    consent_status: str | None = None
    contract_status: str | None = None
    data_volume: str | None = None
    important_data_indicators: List[str] = Field(default_factory=list)
    platform_or_intermediary_role: str | None = None
    missing_facts: List[str] = Field(default_factory=list)
    uncertainty_flags: List[str] = Field(default_factory=list)
    evidence_from_uploaded_material: List[str] = Field(default_factory=list)
    extraction_confidence: str = "low"


class UploadedMaterialFactExtractor:
    PARTY_KW: List[str] = [
        "甲方", "乙方", "提供方", "接收方", "数据提供方", "数据接收方", "转让方", "受让方",
    ]
    PI_KW: List[str] = [
        "个人信息", "个人数据", "用户信息", "客户信息", "用户数据", "个人身份信息",
    ]
    SENSITIVE_KW: List[str] = [
        "敏感个人信息", "敏感数据", "生物识别", "医疗健康", "金融账户", "行踪轨迹",
        "宗教信仰", "特定身份", "未成年人",
    ]
    FINANCE_KW: List[str] = [
        "财务数据", "金融数据", "交易数据", "支付数据", "账户信息", "信用信息", "银行",
    ]
    CROSS_BORDER_KW: List[str] = [
        "出境", "跨境", "境外", "海外", "跨国", "境外接收方", "数据出海", "overseas",
    ]
    TX_KW: List[str] = [
        "数据交易", "数据转让", "数据共享", "数据提供", "数据产品", "数据服务",
    ]
    CONSENT_KW: List[str] = [
        "授权", "同意", "告知", "知情", "用户协议", "隐私政策", "opt-in",
    ]
    CONTRACT_KW: List[str] = [
        "合同", "协议", "条款", "约定", "签署", "标准合同",
    ]
    SECURITY_KW: List[str] = [
        "安全措施", "加密", "脱敏", "匿名化", "访问控制", "审计", "日志", "备份", "防火墙",
    ]
    PLATFORM_KW: List[str] = [
        "平台", "交易所", "中介", "数据交易平台", "数据服务商",
    ]

    def extract(
        self,
        user_prompt: str,
        assessment_type: str,
        intake: Any,
        text_previews: List[str],
    ) -> ExtractedFacts:
        combined = user_prompt + "\n" + "\n".join(text_previews)
        facts = ExtractedFacts()

        facts.parties = self._find_parties(combined, intake)
        facts.data_provider = self._pick(facts.parties, ["提供方", "甲方", "转让方", "数据提供方"])
        facts.data_recipient = self._pick(facts.parties, ["接收方", "乙方", "受让方", "数据接收方"])

        facts.data_categories = self._classify_data(combined)
        facts.personal_information_categories = self._match_all(combined, self.PI_KW)
        facts.sensitive_pi_categories = self._match_all(combined, self.SENSITIVE_KW)

        facts.transaction_type = self._infer_tx_type(combined, assessment_type)
        facts.processing_purpose = self._infer_purposes(combined)
        facts.cross_border_elements = self._match_all(combined, self.CROSS_BORDER_KW)

        if any(kw in combined for kw in ("出境", "跨境")):
            facts.transfer_direction = "cross_border_export"
        elif "境外" in combined:
            facts.transfer_direction = "cross_border_involving"
        else:
            facts.transfer_direction = "domestic"

        facts.recipient_location = self._find_location(combined)
        facts.security_measures = self._match_all(combined, self.SECURITY_KW)
        facts.consent_status = "mentioned" if any(kw in combined for kw in self.CONSENT_KW) else "unknown"
        facts.contract_status = "mentioned" if any(kw in combined for kw in self.CONTRACT_KW) else "unknown"

        if any(kw in combined for kw in ("重要数据", "国家核心数据", "关键信息基础设施")):
            facts.important_data_indicators.append("potential_important_data")

        if any(kw in combined for kw in self.PLATFORM_KW):
            facts.platform_or_intermediary_role = "数据交易平台/中介"

        facts.missing_facts = self._detect_missing(facts, assessment_type)
        facts.uncertainty_flags = self._detect_uncertainties(combined, facts)
        facts.evidence_from_uploaded_material = self._gather_evidence(combined)
        facts.extraction_confidence = self._calc_confidence(facts)

        return facts

    def _find_parties(self, text: str, intake: Any) -> List[str]:
        parties: List[str] = []
        for kw in self.PARTY_KW:
            idx = text.find(kw)
            if idx >= 0:
                snippet = text[idx:idx + 30].strip().replace("\n", " ")
                parties.append(snippet)
        intake_parties = getattr(intake, "parties", []) or []
        for p in intake_parties:
            if p not in parties:
                parties.append(p)
        return list(dict.fromkeys(parties))[:10]

    def _pick(self, parties: List[str], keywords: List[str]) -> str | None:
        for p in parties:
            for kw in keywords:
                if kw in p:
                    return p
        return None

    def _classify_data(self, text: str) -> List[str]:
        cats: List[str] = []
        if any(kw in text for kw in self.FINANCE_KW):
            cats.append("financial_data")
        if any(kw in text for kw in self.PI_KW):
            cats.append("personal_information")
        if any(kw in text for kw in self.SENSITIVE_KW):
            cats.append("sensitive_personal_information")
        if any(kw in text for kw in ("交易数据", "数据交易")):
            cats.append("transaction_data")
        if any(kw in text for kw in self.CROSS_BORDER_KW):
            cats.append("cross_border_data")
        if not cats:
            cats.append("unclassified")
        return cats

    def _match_all(self, text: str, keywords: List[str]) -> List[str]:
        return list({kw for kw in keywords if kw in text})

    def _infer_tx_type(self, text: str, at: str) -> str | None:
        if at == "data_transaction_compliance":
            return "data_transaction"
        if at == "cross_border_data_transfer":
            return "cross_border_data_transfer"
        if at == "pipl_personal_information_protection":
            return "pipl_compliance"
        if "交易" in text:
            return "data_transaction"
        if "跨境" in text or "出境" in text:
            return "cross_border_data_transfer"
        return "general_compliance"

    def _infer_purposes(self, text: str) -> List[str]:
        mapping = {
            "交易": "data_transaction", "共享": "data_sharing",
            "提供": "data_provision", "分析": "data_analysis",
            "处理": "data_processing", "出境": "data_export",
            "传输": "data_transfer", "存储": "data_storage",
        }
        purposes = [v for k, v in mapping.items() if k in text and v not in (
            [p for _k, p in mapping.items() if _k in text and _k != k]
        )]
        purps = list(dict.fromkeys(
            [mapping[k] for k in mapping if k in text]
        ))
        return purps if purps else ["unspecified"]

    def _find_location(self, text: str) -> str | None:
        m = re.search(r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*(?:国|地区)", text)
        if m:
            return m.group(0)
        if "境外" in text or "海外" in text:
            return "境外(未指明具体位置)"
        return None

    def _detect_missing(self, facts: ExtractedFacts, at: str) -> List[str]:
        missing: List[str] = []
        if not facts.parties:
            missing.append("未识别到明确的当事方")
        if not facts.data_provider and not facts.data_recipient:
            missing.append("未识别到数据提供方和接收方")
        if facts.consent_status == "unknown":
            missing.append("未识别到授权/同意信息")
        if facts.contract_status == "unknown":
            missing.append("未识别到合同/协议信息")
        if facts.data_categories == ["unclassified"]:
            missing.append("数据类型信息缺失")
        if not facts.security_measures:
            missing.append("未识别到安全措施信息")
        if facts.personal_information_categories and facts.consent_status == "unknown":
            missing.append("涉及个人信息但缺少授权同意信息")
        if facts.sensitive_pi_categories:
            missing.append("涉及敏感个人信息需更严格合规措施")
        if at == "cross_border_data_transfer" and not facts.cross_border_elements:
            missing.append("跨境评估类型但未识别到明确的跨境元素")
        if not missing:
            missing.append("基于当前材料信息已基本覆盖主要合规维度")
        return missing

    def _detect_uncertainties(self, text: str, facts: ExtractedFacts) -> List[str]:
        flags: List[str] = []
        if not any(kw in text for kw in self.PARTY_KW):
            flags.append("low_confidence: 当事方信息从上下文推断")
        if facts.personal_information_categories and not any(kw in text for kw in self.CONSENT_KW):
            flags.append("medium_risk: 涉及个人信息但未找到同意证据")
        return flags

    def _gather_evidence(self, text: str) -> List[str]:
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        all_kw = self.PARTY_KW + self.PI_KW + self.CROSS_BORDER_KW
        return [ln[:120] for ln in lines if any(kw in ln for kw in all_kw)][:20]

    def _calc_confidence(self, facts: ExtractedFacts) -> str:
        score = sum([
            bool(facts.parties),
            bool(facts.data_categories and facts.data_categories != ["unclassified"]),
            bool(facts.transaction_type),
            facts.consent_status == "mentioned",
            facts.contract_status == "mentioned",
            bool(facts.security_measures),
        ])
        if score >= 5:
            return "medium"
        if score >= 3:
            return "low"
        return "low"