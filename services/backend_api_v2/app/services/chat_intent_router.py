from __future__ import annotations

from typing import List


class ChatIntentRouter:
    def detect(self, message: str, file_ids: List[str] | None = None) -> str:
        text = (message or "").lower()
        has_files = bool(file_ids)
        if any(k in text for k in ["你能做什么", "系统能力", "什么时候会生成", "怎么生成报告", "如何生成报告"]):
            return "system_question"
        if any(k in text for k in ["总结", "概括", "这份材料", "上传材料", "文件内容"]) and has_files:
            return "uploaded_file_summary_question"
        if any(k in text for k in ["生成审查报告", "运行评估", "完整报告", "审查报告"]):
            return "report_request_with_file" if has_files else "report_request_without_file"
        if any(k in text for k in ["第", "条", "条款", "办法", "规定", "个人信息保护法", "数据安全法"]):
            return "regulation_article_question"
        if any(k in text for k in ["法规", "合规", "安全评估", "出境", "跨境", "数据交易", "个人信息"]):
            return "legal_knowledge_question"
        return "general_chat"
