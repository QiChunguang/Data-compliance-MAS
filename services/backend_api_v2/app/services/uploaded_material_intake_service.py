from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.upload import UploadedFile


class UploadedMaterialIntake(BaseModel):
    file_count: int = 0
    file_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    parties: List[str] = Field(default_factory=list)
    data_type: List[str] = Field(default_factory=list)
    transfer_direction: List[str] = Field(default_factory=list)
    cross_border_indicators: List[str] = Field(default_factory=list)
    personal_information_indicators: List[str] = Field(default_factory=list)
    sensitive_pi_indicators: List[str] = Field(default_factory=list)
    transaction_context: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    boundary_warnings: List[str] = Field(default_factory=list)


class UploadedMaterialIntakeService:
    KNOWLEDGE_KEYS: Dict[str, List[str]] = {
        "parties": [
            "甲方", "乙方", "数据提供方", "数据接收方", "委托方", "受托方",
            "个人信息处理者", "数据处理者", "数据交易双方", "出境方", "接收方",
            "party", "data_provider", "data_recipient", "controller", "processor",
        ],
        "data_type": [
            "个人信息", "敏感个人信息", "交易数据", "业务数据", "用户数据",
            "金融数据", "医疗数据", "轨迹数据", "身份信息", "信用信息",
            "personal", "sensitive", "financial", "medical", "biometric",
        ],
        "transfer_direction": [
            "跨境", "出境", "境内", "境外", "跨国", "国际",
            "cross_border", "overseas", "international", "domestic",
        ],
        "cross_border": [
            "跨境传输", "数据出境", "标准合同", "安全评估", "认证",
            "个人信息出境", "重要数据出境", "境外接收方",
        ],
        "personal_information": [
            "个人信息", "PIPL", "个人信息保护法", "告知同意", "最小必要",
            "单独同意", "撤回同意", "删除权", "更正权", "可携带权",
        ],
        "sensitive_pi": [
            "敏感个人信息", "生物识别", "医疗健康", "金融账户", "行踪轨迹",
            "不满十四周岁", "未成年人", "单独同意", "必要",
        ],
        "transaction_context": [
            "数据交易", "委托处理", "共享", "转让", "公开", "提供",
            "数据流通", "数据服务", "数据处理", "数据分析",
        ],
    }

    def intake(self, files: List[UploadedFile], user_prompt: str = "") -> UploadedMaterialIntake:
        intake = UploadedMaterialIntake(file_count=len(files))
        intake.boundary_warnings = [
            "uploaded files are preview_only/intake_only",
            "files are NOT written to Chroma/Neo4j/current_backend",
            "uploaded materials do NOT represent source-backed evidence",
            "manual verification is NOT performed",
        ]

        combined_text = user_prompt
        for f in files:
            summary = {
                "file_id": f.file_id,
                "original_filename": f.original_filename,
                "parse_status": f.parse_status,
                "size_bytes": f.size_bytes,
            }
            if f.text_preview:
                preview = f.text_preview[:3000]
                summary["text_preview_length"] = len(preview)
                combined_text += "\n" + preview
            intake.file_summaries.append(summary)

        if combined_text.strip():
            for category, keys in self.KNOWLEDGE_KEYS.items():
                found = self._scan_keys(combined_text, keys)
                if category in ("cross_border",):
                    if found:
                        intake.cross_border_indicators.extend(found)
                elif category in ("personal_information",):
                    if found:
                        intake.personal_information_indicators.extend(found)
                elif category in ("sensitive_pi",):
                    if found:
                        intake.sensitive_pi_indicators.extend(found)
                else:
                    target = getattr(intake, category, None)
                    if target is not None and found:
                        target.extend(found)

        if not intake.parties:
            intake.parties.append("未明确识别（建议补充交易方信息）")
        if not intake.data_type:
            intake.data_type.append("未明确识别（建议补充数据类型说明）")
        if not intake.transfer_direction:
            intake.transfer_direction.append("未明确识别")

        intake.missing_information = self._detect_missing(intake)
        return intake

    def _scan_keys(self, text: str, keys: List[str]) -> List[str]:
        found: List[str] = []
        for key in keys:
            if key.lower() in text.lower():
                if key not in found:
                    found.append(key)
        return found

    def _detect_missing(self, intake: UploadedMaterialIntake) -> List[str]:
        missing: List[str] = []
        if not any(p != "未明确识别（建议补充交易方信息）" for p in intake.parties):
            missing.append("交易主体信息缺失")
        if not any(d != "未明确识别（建议补充数据类型说明）" for d in intake.data_type):
            missing.append("数据类型信息缺失")
        if not intake.transaction_context:
            missing.append("交易/处理场景信息不足")
        if not intake.cross_border_indicators and not intake.transfer_direction:
            missing.append("跨境传输信息未识别")
        if not intake.personal_information_indicators:
            missing.append("个人信息处理相关信息未识别")
        if not missing:
            missing.append("初步材料检查通过，仍建议补充完整业务底稿")
        return missing