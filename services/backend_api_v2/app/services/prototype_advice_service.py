from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from app.models.assessment import ASSESSMENT_DESCRIPTIONS, AssessmentType
from app.services.assessment_intent_service import AssessmentIntent
from app.services.uploaded_material_intake_service import UploadedMaterialIntake


class PrototypeAdvice(BaseModel):
    identified_issues: List[str] = Field(default_factory=list)
    material_gaps: List[str] = Field(default_factory=list)
    preliminary_concerns: List[str] = Field(default_factory=list)
    suggested_supplements: List[str] = Field(default_factory=list)
    can_run_diagnostic: bool = True
    boundary_notice: str = ""


class PrototypeAdviceService:
    ASSESSMENT_SCOPES: Dict[AssessmentType, Dict[str, List[str]]] = {
        AssessmentType.data_transaction_compliance: {
            "issues": [
                "数据交易主体的合规资质",
                "交易数据的确权与合法性",
                "数据产品/服务的定价与交易条件",
                "数据交易平台的合规义务",
            ],
            "supplements": [
                "交易合同或意向书",
                "数据产品说明书",
                "交易平台资质文件",
                "数据来源合法性说明",
            ],
        },
        AssessmentType.data_flow_security_review: {
            "issues": [
                "数据流通链路的安全性",
                "数据共享的授权与边界",
                "数据传输的加密与访问控制",
                "数据接口的安全防护",
            ],
            "supplements": [
                "数据流通流程图",
                "安全技术措施说明",
                "访问控制策略文档",
                "数据共享协议",
            ],
        },
        AssessmentType.cross_border_data_transfer: {
            "issues": [
                "数据出境的安全评估要求",
                "个人信息出境的告知同意",
                "重要数据出境的审批流程",
                "境外接收方的保护水平",
            ],
            "supplements": [
                "数据出境申请书",
                "个人信息保护影响评估报告",
                "标准合同或认证文件",
                "境外接收方安全保障说明",
            ],
        },
        AssessmentType.pipl_personal_information_protection: {
            "issues": [
                "个人信息处理的合法性基础",
                "告知同意的合规性",
                "敏感个人信息的单独同意",
                "个人信息主体的权利保障",
            ],
            "supplements": [
                "隐私政策文本",
                "个人信息处理规则",
                "数据保护影响评估",
                "用户同意记录机制说明",
            ],
        },
        AssessmentType.general_data_compliance_diagnostic: {
            "issues": [
                "数据处理活动的合规性概述",
                "适用的法律法规识别",
                "潜在的合规风险点",
            ],
            "supplements": [
                "数据清单或目录",
                "数据处理活动记录",
                "组织架构与职责说明",
            ],
        },
    }

    def generate(
        self,
        assessment_type: AssessmentType,
        user_message: str,
        intake: UploadedMaterialIntake,
        intent: AssessmentIntent,
    ) -> PrototypeAdvice:
        scope = self.ASSESSMENT_SCOPES.get(assessment_type, self.ASSESSMENT_SCOPES[AssessmentType.general_data_compliance_diagnostic])

        identified_issues = list(scope.get("issues", []))
        material_gaps = list(intake.missing_information)
        suggested_supplements = list(scope.get("supplements", []))

        concerns: List[str] = []
        if assessment_type in (AssessmentType.cross_border_data_transfer,):
            if not intake.cross_border_indicators:
                concerns.append("未检测到明确的跨境传输指标，建议补充跨境数据传输途径和接收方信息。")
        if assessment_type in (AssessmentType.pipl_personal_information_protection,):
            if not intake.personal_information_indicators:
                concerns.append("未检测到个人信息处理相关指标，建议补充个人信息处理的具体场景和目的。")
        if assessment_type == AssessmentType.data_transaction_compliance:
            if not intake.transaction_context:
                concerns.append("未检测到数据交易场景描述，建议补充交易类型、交易平台和交易标的。")

        if not intake.file_summaries:
            concerns.insert(0, "未上传任何材料，建议上传相关业务文件以获得更有针对性的分析。")
            material_gaps.insert(0, "未上传材料，建议上传合同、隐私政策、数据处理协议等文件。")

        boundary_notice = (
            "这是 prototype diagnostic 初步分析，不是正式法律意见。"
            "当前分析基于 dry-run 模式，上传材料仅进入 runtime_storage，未写入 Chroma/Neo4j/current_backend。"
            "建议补充完整业务底稿后重新运行评估。"
        )

        return PrototypeAdvice(
            identified_issues=identified_issues,
            material_gaps=material_gaps,
            preliminary_concerns=concerns or ["未发现明显问题，建议补充更多材料后进行深入分析。"],
            suggested_supplements=suggested_supplements,
            can_run_diagnostic=True,
            boundary_notice=boundary_notice,
        )

    def format_assistant_reply(
        self,
        advice: PrototypeAdvice,
        assessment_type: AssessmentType,
        intent: AssessmentIntent,
        intake: UploadedMaterialIntake,
    ) -> str:
        label = ASSESSMENT_DESCRIPTIONS.get(assessment_type, str(assessment_type))
        lines: List[str] = []
        lines.append("## 🔍 Prototype Diagnostic 分析结果")
        lines.append("")
        lines.append(f"**评估类型**：{label}")
        if intent.confidence != "explicit":
            lines.append(f"**识别置信度**：{intent.confidence}（{intent.recommendation}）")

        lines.append("")
        lines.append("### ✅ 已识别的问题")
        for issue in advice.identified_issues:
            lines.append(f"- {issue}")

        if advice.preliminary_concerns:
            lines.append("")
            lines.append("### ⚠️ 初步合规关注点")
            for concern in advice.preliminary_concerns:
                lines.append(f"- {concern}")

        if advice.material_gaps:
            lines.append("")
            lines.append("### 📋 当前材料缺口")
            for gap in advice.material_gaps:
                lines.append(f"- {gap}")

        if advice.suggested_supplements:
            lines.append("")
            lines.append("### 📎 建议补充材料")
            for supp in advice.suggested_supplements:
                lines.append(f"- {supp}")

        if intake.file_summaries:
            lines.append("")
            lines.append("### 📁 已上传材料摘要")
            for s in intake.file_summaries:
                lines.append(f"- `{s.get('original_filename', 'unknown')}` ({s.get('parse_status', 'unknown')})")

        lines.append("")
        lines.append("### 🛡️ 系统边界")
        lines.append(advice.boundary_notice)
        lines.append("")
        lines.append("您可以点击「评估」按钮发起 prototype diagnostic 评估，或继续补充材料后重新提问。")

        return "\n".join(lines)