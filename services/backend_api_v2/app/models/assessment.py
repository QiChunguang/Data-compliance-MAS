from __future__ import annotations

from enum import StrEnum
from typing import Dict

from pydantic import BaseModel


class AssessmentType(StrEnum):
    data_transaction_compliance = "data_transaction_compliance"
    data_flow_security_review = "data_flow_security_review"
    cross_border_data_transfer = "cross_border_data_transfer"
    pipl_personal_information_protection = "pipl_personal_information_protection"
    general_data_compliance_diagnostic = "general_data_compliance_diagnostic"


ASSESSMENT_DESCRIPTIONS: Dict[AssessmentType, str] = {
    AssessmentType.data_transaction_compliance: "数据交易合规评估",
    AssessmentType.data_flow_security_review: "数据流通安全审查",
    AssessmentType.cross_border_data_transfer: "跨境数据传输评估",
    AssessmentType.pipl_personal_information_protection: "PIPL 个人信息保护评估",
    AssessmentType.general_data_compliance_diagnostic: "通用数据合规诊断",
}


class AssessmentTypeInfo(BaseModel):
    assessment_type: AssessmentType
    label: str
    description: str
