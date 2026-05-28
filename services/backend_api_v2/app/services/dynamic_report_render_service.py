from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class DynamicReportRenderService:
    def render(self, case_id: str, assessment_type: str, user_prompt: str,
               facts: Any, profile: Any, route: Any,
               claims: List[Dict], evidence_pack: Any,
               citations: List[Dict], risk_score: Any,
               autojudge_result: Dict | None = None,
               retrieval_trace: Any = None,
               source_trace: Any = None,
               bridge_result: Dict | None = None) -> str:
        now = datetime.utcnow().isoformat()

        facts_dict = facts.model_dump(mode="json") if hasattr(facts, "model_dump") else facts

        lines = [
            "# ReguThink 多智能体数据合规评估报告",
            "",
            "---",
            "",
            "> **⚠️ 非正式法律意见声明**",
            "> ",
            "> 本报告由 ReguThink 多智能体合规系统自动生成，",
            "> 属于 prototype diagnostic 原型诊断结果，**不构成正式法律意见**。",
            "> ",
            "> - 上传材料仅作为业务事实参考（business_facts_only）",
            "> - 法律引用来自规则型领域知识匹配与只读法规检索",
            "> - 所有结论未经人工审核",
            "> - 所有引用未经文章级别验证",
            "> - 上传材料未写入 Chroma/Neo4j/current_backend",
            "> ",
            "> 如需正式法律意见，请咨询持证律师。",
            "",
            "---",
            "",
            "## 1. 评估概述",
            "",
            f"| 项目 | 内容 |",
            f"|------|------|",
            f"| 评估类型 | {assessment_type} |",
            f"| 伪用例ID | {case_id} |",
            f"| 支持级别 | {getattr(route, 'support_level', 'prototype') if route else 'prototype'} |",
            f"| 生成时间 | {now} |",
            "",
            "## 2. 用户输入与材料清单",
            "",
            f"### 2.1 用户输入",
            f"```",
            f"{user_prompt[:500]}",
            f"```",
            "",
            "### 2.2 材料清单",
            "",
            "### 上传材料摘要",
            "",
            "上传材料仅用于识别业务事实、交易结构、数据类型、处理目的、授权状态和安全措施，不作为法律依据或已核验证据。",
        ]

        evidence_from_mat = facts_dict.get("evidence_from_uploaded_material", []) if isinstance(facts_dict, dict) else []
        if evidence_from_mat:
            for idx, ev in enumerate(evidence_from_mat[:10]):
                lines.append(f"{idx+1}. {str(ev)[:200]}")

        lines.extend([
            "",
            "## 3. 事实识别结果",
            "",
            "### 事实摘要",
            "",
            f"- **当事方**: {facts_dict.get('parties', []) if isinstance(facts_dict, dict) else '未识别'}",
            f"- **数据类型**: {facts_dict.get('data_categories', []) if isinstance(facts_dict, dict) else '未识别'}",
            f"- **个人信息**: {facts_dict.get('personal_information_categories', []) if isinstance(facts_dict, dict) else '无'}",
            f"- **敏感个人信息**: {facts_dict.get('sensitive_pi_categories', []) if isinstance(facts_dict, dict) else '无'}",
            f"- **跨境元素**: {facts_dict.get('cross_border_elements', []) if isinstance(facts_dict, dict) else '无'}",
            f"- **传输方向**: {facts_dict.get('transfer_direction', '未确定') if isinstance(facts_dict, dict) else '未确定'}",
            f"- **授权状态**: {facts_dict.get('consent_status', '未知') if isinstance(facts_dict, dict) else '未知'}",
            f"- **合同状态**: {facts_dict.get('contract_status', '未知') if isinstance(facts_dict, dict) else '未知'}",
            f"- **安全措施**: {facts_dict.get('security_measures', []) if isinstance(facts_dict, dict) else '未识别'}",
            f"- **提取置信度**: {facts_dict.get('extraction_confidence', 'low') if isinstance(facts_dict, dict) else 'low'}",
            "",
            "## 4. 评估路径与运行轨迹",
            "",
            f"- **路径**: {getattr(route, 'route', 'unknown') if route else 'unknown'}",
            f"- **选中的智能体**: {getattr(route, 'selected_agents', []) if route else []}",
            f"- **选中的法律领域**: {getattr(route, 'selected_legal_domains', []) if route else []}",
            "",
            "## 5. 核心合规问题分析",
        ])

        for c in claims:
            cd = c if isinstance(c, dict) else (c.model_dump() if hasattr(c, 'model_dump') else {})
            cid = cd.get("claim_id", "") if isinstance(cd, dict) else ""
            title = cd.get("title", cd.get("claim_text", "")) if isinstance(cd, dict) else ""
            check = cd.get("check", "") if isinstance(cd, dict) else ""
            domain = cd.get("domain", "") if isinstance(cd, dict) else ""
            lines.append(f"### [{cid}] {title}")
            lines.append(f"- 分析范围: {domain}")
            lines.append(f"- 核查要点: {check}")
            lines.append("")

        lines.extend([
            "### 分项分析",
            "- 业务事实、法律规则、证据边界和整改建议分别列示；上传材料只用于事实识别。",
            "- 法律依据仅来自只读法规库/RAG/source trace，不以上传材料作为法律依据。",
            "- 对于未能通过 source trace 完成验证的结论，保持 needs_manual_verification。",
            "",
        ])

        lines.extend([
            "## 6. 适用规则与证据",
            "",
            "> 以下法律引用基于规则型领域知识匹配和只读法规检索，",
            "> 未经文章级别验证和人工审核。",
        ])

        seen_citations = set()
        for c in citations:
            cd = c if isinstance(c, dict) else (c.model_dump() if hasattr(c, 'model_dump') else {})
            if isinstance(cd, dict):
                law = cd.get("law_reference", cd.get("source_id", ""))
                if law and law not in seen_citations:
                    seen_citations.add(law)
                    lines.append(f"- **{law}**: {cd.get('content', '')[:200]}")

        lines.extend(self._render_risk_section(risk_score))
        lines.extend(self._render_autojudge_section(autojudge_result))
        lines.extend(self._render_evidence_boundary(evidence_pack, retrieval_trace))
        lines.extend(self._render_missing_section(facts_dict))
        lines.extend(self._render_boundary_statement(bridge_result))
        lines.append("")
        lines.append("---")
        lines.append(f"*ReguThink 多智能体合规系统 · {now} · Prototype Diagnostic Only*")

        return "\n".join(lines)

    def render_from_bridge(self, bridge_report: str) -> str:
        if bridge_report and len(bridge_report) > 200:
            return bridge_report
        return self.render("bridge_case", "unknown", "", {}, None, None, [], {}, [], None)

    def _render_risk_section(self, risk_score: Any) -> List[str]:
        risk_dict = risk_score.model_dump(mode="json") if hasattr(risk_score, "model_dump") else (risk_score if isinstance(risk_score, dict) else {})
        lines = [
            "",
            "## 7. 风险分级",
            "",
            f"- **综合风险等级**: **{risk_dict.get('overall_risk_level', 'unknown')}**",
            f"- 数据交易风险: {risk_dict.get('transaction_risk', {}).get('level', 'unknown')}",
            f"- 个人信息保护风险: {risk_dict.get('personal_information_risk', {}).get('level', 'unknown')}",
            f"- 敏感PI风险: {risk_dict.get('sensitive_pi_risk', {}).get('level', 'unknown')}",
            f"- 跨境风险: {risk_dict.get('cross_border_risk', {}).get('level', 'unknown')}",
            f"- 证据缺口风险: {risk_dict.get('evidence_gap_risk', {}).get('level', 'unknown')}",
            f"- Source Trace风险: {risk_dict.get('source_trace_risk', {}).get('level', 'unknown')}",
            f"- 置信度: {risk_dict.get('confidence', 'low')}",
            "",
        ]

        actions = risk_dict.get("recommended_actions", [])
        if actions:
            lines.append("### 建议行动")
            for a in actions:
                lines.append(f"- {a}")
            lines.append("")

        return lines

    def _render_autojudge_section(self, autojudge_result: Dict | None) -> List[str]:
        if not autojudge_result:
            return [
                "",
                "## 8. AutoJudge 评分",
                "",
                "> ⚠️ AutoJudge 评分未生成（autojudge_result unavailable）。",
                "",
            ]

        lines = [
            "",
            "## 8. AutoJudge 评分",
            "",
            "### AutoJudge 评分摘要",
            "",
        ]

        aj = autojudge_result
        if isinstance(aj, dict):
            overall = aj.get("overall_score", aj.get("final_score", "N/A"))
            grade = aj.get("grade", aj.get("letter_grade", "N/A"))
            lines.extend([
                f"- **综合评分**: {overall}",
                f"- **评级**: {grade}",
                f"- **评分来源**: {aj.get('scoring_mode', aj.get('source', 'unknown'))}",
            ])

            breakdown = aj.get("score_breakdown", aj.get("dimension_scores", {}))
            if breakdown and isinstance(breakdown, dict):
                lines.append("")
                lines.append("### 维度评分")
                for dim, score in breakdown.items():
                    lines.append(f"- {dim}: {score}")

            caps = aj.get("caps", aj.get("cap_results", []))
            if caps:
                lines.append("")
                lines.append("### 评分限制")
                for c in caps if isinstance(caps, list) else [caps]:
                    lines.append(f"- {c}")

        lines.append("")
        return lines

    def _render_evidence_boundary(self, evidence_pack: Any, retrieval_trace: Any) -> List[str]:
        lines = [
            "",
            "## 9. 证据边界与 source trace 摘要",
            "",
        ]

        if retrieval_trace and hasattr(retrieval_trace, "fallback_used"):
            fb = retrieval_trace.fallback_used
            mode = retrieval_trace.backend_type if hasattr(retrieval_trace, 'backend_type') else "unknown"
            lines.append(f"- 检索模式: {'fallback (规则型)' if fb else f'Chroma 向量检索 ({mode})'}")
            lines.append(f"- 查询集合: {getattr(retrieval_trace, 'collections_queried', [])}")

        lines.extend([
            "- 法律来源核验状态: 未经人工核查",
            "- 人工审核状态: 未审核",
            "- 条文级核验状态: 未逐条验证",
            "- 上传材料未写入 Chroma/Neo4j",
            "- legal_data/current_backend 未被修改",
            "",
        ])
        return lines

    def _render_missing_section(self, facts_dict: Any) -> List[str]:
        lines = [
            "## 10. 缺失材料与补充建议",
            "",
            "### 待补充材料",
        ]
        missing = facts_dict.get("missing_facts", []) if isinstance(facts_dict, dict) else []
        if missing:
            for m in missing:
                lines.append(f"- {m}")
        else:
            lines.append("- 初步材料检查通过，仍建议补充完整业务底稿")

        lines.extend([
            "",
            "### 建议补充材料",
            "- 完整的交易合同或意向书",
            "- 数据产品说明书",
            "- 数据来源合法性说明",
            "- 个人信息处理的告知同意证明",
            "- 敏感个人信息处理的单独同意证明",
            "- 数据安全保护措施的技术文档",
            "",
        ])
        return lines

    def _render_boundary_statement(self, bridge_result: Dict | None) -> List[str]:
        lines = [
            "## 11. 系统边界与限制声明",
            "",
            "- **prototype_diagnostic**: 本报告为原型诊断，非正式法律意见",
            "- **法律来源核验**: 法律来源未经人工核查",
            "- **人工审核**: 评估结果未经人工审核",
            "- **条文级核验**: 法律条文未经逐条验证",
            "- **uploaded_files_not_written_to_chroma**: 上传文件未写入向量数据库",
            "- **uploaded_files_not_written_to_neo4j**: 上传文件未写入图数据库",
            "- **current_backend_not_modified**: 法规数据库未被修改",
            "- **rules_based_extraction**: 事实抽取基于规则型关键词匹配",
            "",
        ]
        if bridge_result:
            bridge_trace = bridge_result.get("bridge_trace", [])
            if bridge_trace:
                lines.append("### Bridge 调用追踪")
                for t in bridge_trace[:5]:
                    lines.append(f"- {t.get('module', '')}: {'成功' if t.get('call_successful') else '回退'} ({t.get('fallback_reason', '')[:100]})")
                lines.append("")
        return lines
