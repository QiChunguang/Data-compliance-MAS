from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List


class UserReportRenderService:
    """Render business-readable reports without exposing runtime diagnostics."""

    def render(
        self,
        *,
        assessment_type: str,
        user_prompt: str,
        facts: Any,
        claims: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        risk_score: Any,
        evidence_pack: Any,
        retrieval_trace: Any,
        file_records: List[Any],
    ) -> str:
        facts_dict = facts.model_dump(mode="json") if hasattr(facts, "model_dump") else (facts if isinstance(facts, dict) else {})
        risk_dict = risk_score.model_dump(mode="json") if hasattr(risk_score, "model_dump") else (risk_score if isinstance(risk_score, dict) else {})
        evidence_dict = evidence_pack.model_dump(mode="json") if hasattr(evidence_pack, "model_dump") else (evidence_pack if isinstance(evidence_pack, dict) else {})
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        material_rows = [
            f"- {getattr(item, 'original_filename', '业务材料')}：{getattr(item, 'parse_status', '已解析')}，仅作为业务事实输入。"
            for item in file_records
        ] or ["- 当前报告基于用户问题和已提供的会话材料生成。"]

        fact_lines = self._fact_lines(facts_dict)
        legal_basis = self._legal_basis(citations)
        risk_lines = self._risk_lines(risk_dict, claims)
        evidence_lines = self._evidence_lines(evidence_dict, retrieval_trace)
        recommendation_lines = self._recommendations(risk_dict, facts_dict)

        lines = [
            "# ReguThink 合规审查辅助报告",
            "",
            f"生成时间：{now}",
            "",
            "## 审查对象与材料范围",
            "",
            f"- 审查类型：{self._label_assessment(assessment_type)}",
            f"- 用户问题：{self._clean_text(user_prompt, 260)}",
            *material_rows,
            "- 上传材料仅用于识别业务事实，不写入法规库、向量库、图数据库或后端指针文件。",
            "",
            "## 业务事实摘要",
            "",
            *fact_lines,
            "",
            "## 适用法律依据",
            "",
            *legal_basis,
            "",
            "## 核心合规风险",
            "",
            *risk_lines,
            "",
            "## 证据与引用",
            "",
            *evidence_lines,
            "",
            "## 整改建议",
            "",
            *recommendation_lines,
            "",
            "## 证据边界与人工复核状态",
            "",
            "- 法律依据来自只读合规知识库检索结果和系统内置合规规则。",
            "- 上传材料只作为业务事实输入，不作为法律依据本身。",
            "- 当前人工复核状态：未复核。",
            "- 本报告未声明人工复核完成、人工验证完成或条文级人工核验完成。",
            "- 若用于正式工作流，应由法务、合规人员或外部律师复核后再采信。",
            "",
            "## 免责声明",
            "",
            "本报告为 ReguThink 自动生成的非正式合规辅助分析，仅用于业务沟通和合规初筛，不构成正式法律意见。正式结论应以人工复核、完整材料核验以及适用法律法规的最新有效文本为准。",
            "",
        ]
        return "\n".join(lines)

    def _label_assessment(self, assessment_type: str) -> str:
        labels = {
            "data_transaction_compliance": "数据交易合规审查",
            "cross_border_data_transfer": "数据出境与跨境传输合规审查",
            "personal_information_protection": "个人信息保护合规审查",
            "general_data_compliance_diagnostic": "通用数据合规审查",
        }
        return labels.get(str(assessment_type), "数据合规审查")

    def _fact_lines(self, facts: Dict[str, Any]) -> List[str]:
        fields = [
            ("当事方", facts.get("parties")),
            ("数据类型", facts.get("data_categories") or facts.get("data_type")),
            ("个人信息相关内容", facts.get("personal_information_categories")),
            ("敏感个人信息相关内容", facts.get("sensitive_pi_categories")),
            ("跨境因素", facts.get("cross_border_elements")),
            ("传输方向", facts.get("transfer_direction")),
            ("授权与同意状态", facts.get("consent_status")),
            ("合同状态", facts.get("contract_status")),
            ("安全措施", facts.get("security_measures")),
        ]
        lines = [f"- {label}：{self._format_value(value)}" for label, value in fields if self._has_value(value)]
        missing = facts.get("missing_facts") or []
        if missing:
            lines.append(f"- 待补充信息：{self._format_value(missing[:6])}")
        return lines or ["- 现有材料中的业务事实仍需进一步补充和人工确认。"]

    def _legal_basis(self, citations: Iterable[Dict[str, Any]]) -> List[str]:
        rows: List[str] = []
        seen = set()
        fallback_index = 1
        for item in citations:
            if not isinstance(item, dict):
                continue
            title = item.get("law_reference") or item.get("source_title") or item.get("title") or item.get("law_name")
            content = item.get("content") or item.get("text") or item.get("snippet") or ""
            if self._looks_like_raw_identifier(title):
                title = f"法规依据 {fallback_index}"
                fallback_index += 1
            if self._looks_like_raw_identifier(content):
                content = "该依据来自只读合规知识库，需在人工复核阶段确认条文名称、效力层级和适用关系。"
            if not title or title in seen:
                continue
            seen.add(title)
            suffix = f"：{self._clean_text(str(content), 160)}" if content else ""
            rows.append(f"- {self._clean_text(str(title), 120)}{suffix}")
            if len(rows) >= 8:
                break
        return rows or ["- 系统未形成可直接展示的具体条文摘要；建议在人工复核阶段补充核验适用依据。"]

    def _risk_lines(self, risk: Dict[str, Any], claims: List[Dict[str, Any]]) -> List[str]:
        overall = risk.get("overall_risk_level") or risk.get("risk_level") or "待人工判断"
        lines = [f"- 综合风险提示：{overall}。"]
        for claim in claims[:6]:
            if not isinstance(claim, dict):
                continue
            title = claim.get("title") or claim.get("claim_text") or claim.get("claim_id")
            check = claim.get("check") or claim.get("description")
            if title:
                if "_" in str(title) or any(token in str(title) for token in ["data categories", "personal information", "data_compliance"]):
                    title = "处理活动与义务匹配风险"
                if check and any(token in str(check) for token in ["data categories", "personal information", "data_compliance", "parties"]):
                    check = "需补充交易方、数据字段、个人信息处理目的、授权依据、保存期限和安全控制材料后再进入正式复核。"
                lines.append(f"- {self._clean_text(str(title), 80)}：{self._clean_text(str(check or '需结合材料进一步核验'), 140)}")
        return lines

    def _evidence_lines(self, evidence: Dict[str, Any], retrieval_trace: Any) -> List[str]:
        items = evidence.get("evidence_items") or evidence.get("evidence_rows") or []
        lines: List[str] = []
        for index, item in enumerate(items[:8], start=1):
            if not isinstance(item, dict):
                continue
            title = item.get("source_title") or item.get("title") or item.get("law_reference") or "证据条目"
            text = item.get("content") or item.get("snippet") or item.get("evidence_text") or ""
            if self._looks_like_raw_identifier(title) or self._looks_like_raw_identifier(text):
                title = f"证据摘要 {index}"
                text = "该条证据来自只读合规知识库，需在人工复核阶段核验其与业务事实的对应关系。"
            lines.append(f"- {self._clean_text(str(title), 100)}：{self._clean_text(str(text), 160)}")
        if lines:
            return lines
        total = getattr(retrieval_trace, "total_items", 0) if retrieval_trace is not None else 0
        if total:
            return [f"- 系统检索到 {total} 条候选依据，需在人工复核阶段确认其与业务事实的对应关系。"]
        return ["- 当前证据摘要不足，建议补充材料并进行人工复核。"]

    def _recommendations(self, risk: Dict[str, Any], facts: Dict[str, Any]) -> List[str]:
        actions = risk.get("recommended_actions") or []
        lines = [f"- {self._clean_text(str(item), 180)}" for item in actions[:8]]
        if lines:
            return lines
        missing = facts.get("missing_facts") or []
        base = [
            "- 补充数据来源、授权同意、处理目的、接收方和安全措施说明。",
            "- 对涉及个人信息或敏感个人信息的处理活动开展专项合规复核。",
            "- 将合同、告知同意、影响评估和安全控制证据纳入人工复核材料包。",
        ]
        if missing:
            base.append("- 优先补充待确认事实后再进入正式审查流程。")
        return base

    def _format_value(self, value: Any) -> str:
        if isinstance(value, list):
            return "、".join(self._clean_text(str(item), 80) for item in value[:8]) if value else "未明确"
        if isinstance(value, dict):
            return "；".join(f"{self._clean_text(str(k), 40)}：{self._clean_text(str(v), 80)}" for k, v in list(value.items())[:6])
        return self._clean_text(str(value), 160)

    def _has_value(self, value: Any) -> bool:
        return value not in (None, "", [], {})

    def _looks_like_raw_identifier(self, value: Any) -> bool:
        text = str(value or "")
        return "src_" in text or "source_id" in text or "article_id" in text or "doc_" in text

    def _clean_text(self, text: str, limit: int) -> str:
        forbidden = [
            "runtime", "manifest", "AutoJudge", "autojudge", "prototype", "dry-run", "full-chain",
            "support_level", "needs_manual_verification", "source_backed=true", "manual_verified=true",
            "article_level_verified=true", "human_reviewed=true", "BGE", "bge_m3", "reranker", "vector_top_k",
        ]
        cleaned = (text or "").replace("\r", " ").replace("\n", " ").replace("|", " ")
        for token in forbidden:
            cleaned = cleaned.replace(token, "内部字段")
        return cleaned.strip()[:limit] or "未明确"
