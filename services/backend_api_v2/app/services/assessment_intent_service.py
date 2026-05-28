from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.assessment import ASSESSMENT_DESCRIPTIONS, AssessmentType


class AssessmentIntent(BaseModel):
    detected_type: AssessmentType = AssessmentType.general_data_compliance_diagnostic
    confidence: str = "low"
    matched_keywords: List[str] = Field(default_factory=list)
    suggested_types: List[Dict[str, str]] = Field(default_factory=list)
    recommendation: str = ""


class AssessmentIntentService:
    INTENT_KEYWORDS: Dict[AssessmentType, List[str]] = {
        AssessmentType.data_transaction_compliance: [
            "数据交易", "数据买卖", "数据资产", "数据产品", "数据撮合",
            "交易平台", "数据确权", "定价", "交易合规", "数据交易所",
            "data transaction", "data trade", "data asset",
        ],
        AssessmentType.data_flow_security_review: [
            "数据流通", "数据共享", "数据流转", "数据开放", "数据交换",
            "流通安全", "共享安全", "数据接口", "API安全", "数据传输",
            "data flow", "data sharing", "data exchange",
        ],
        AssessmentType.cross_border_data_transfer: [
            "跨境", "出境", "数据传输", "境外", "跨国", "标准合同",
            "安全评估", "数据出境安全", "个人信息出境", "重要数据",
            "cross border", "overseas transfer", "data export",
        ],
        AssessmentType.pipl_personal_information_protection: [
            "个人信息", "PIPL", "个人信息保护法", "隐私政策", "告知同意",
            "单独同意", "撤回同意", "删除权", "更正权", "可携带权",
            "敏感个人信息", "未成年", "个人信息处理者",
            "personal information", "PIPL", "privacy", "consent",
        ],
        AssessmentType.general_data_compliance_diagnostic: [
            "合规", "数据合规", "法规", "监管", "评估", "诊断",
            "compliance", "regulatory", "assessment",
        ],
    }

    def detect(self, user_message: str, selected_type: Optional[AssessmentType] = None) -> AssessmentIntent:
        if selected_type and selected_type != AssessmentType.general_data_compliance_diagnostic:
            return AssessmentIntent(
                detected_type=selected_type,
                confidence="explicit",
                matched_keywords=[],
                suggestion=f"用户已选择 {ASSESSMENT_DESCRIPTIONS.get(selected_type, str(selected_type))}",
            )

        best_type = AssessmentType.general_data_compliance_diagnostic
        best_score = 0
        all_matches: Dict[str, int] = {}

        for assessment_type, keywords in self.INTENT_KEYWORDS.items():
            score = 0
            matched = []
            for kw in keywords:
                if kw.lower() in user_message.lower():
                    score += 1
                    matched.append(kw)
            all_matches[str(assessment_type)] = score
            if score > best_score:
                best_score = score
                best_type = assessment_type

        confidence = "low"
        if best_score >= 4:
            confidence = "high"
        elif best_score >= 2:
            confidence = "medium"

        matched_keywords: List[str] = []
        for kw in self.INTENT_KEYWORDS.get(best_type, []):
            if kw.lower() in user_message.lower():
                matched_keywords.append(kw)

        suggested_types: List[Dict[str, str]] = []
        for t, score in sorted(all_matches.items(), key=lambda x: x[1], reverse=True):
            if score > 0:
                suggested_types.append({
                    "assessment_type": t,
                    "label": ASSESSMENT_DESCRIPTIONS.get(AssessmentType(t), t),
                    "match_score": str(score),
                })

        return AssessmentIntent(
            detected_type=best_type,
            confidence=confidence,
            matched_keywords=matched_keywords,
            suggested_types=suggested_types,
            recommendation=self._build_recommendation(best_type, confidence),
        )

    def _build_recommendation(self, assessment_type: AssessmentType, confidence: str) -> str:
        label = ASSESSMENT_DESCRIPTIONS.get(assessment_type, str(assessment_type))
        if confidence == "high":
            return f"根据您的输入，建议选择「{label}」。如果不符合，您可以手动切换评估类型。"
        elif confidence == "medium":
            return f"您的输入可能涉及「{label}」，建议确认评估类型是否准确。"
        return f"当前选择「{label}」。您可以从评估类型选择器中手动切换更精确的类型。"