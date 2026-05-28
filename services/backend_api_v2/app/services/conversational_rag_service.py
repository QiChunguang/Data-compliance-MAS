from __future__ import annotations

from typing import Any, Dict, List

from app.services.legal_retrieval_runtime_service import LegalRetrievalRuntimeService


class ConversationalRAGService:
    LEGAL_KEYWORDS = (
        "法规", "法律", "条款", "合规", "出境", "跨境", "个人信息", "安全评估",
        "标准合同", "数据交易", "数据流通", "PIPL", "RAG", "source",
    )

    def __init__(self) -> None:
        self.retrieval = LegalRetrievalRuntimeService()

    def should_retrieve(self, message: str, intent: str, rag_enabled: bool) -> bool:
        if not rag_enabled:
            return False
        if intent in {"legal_knowledge_question", "regulation_article_question"}:
            return True
        lowered = message.lower()
        return any(keyword.lower() in lowered for keyword in self.LEGAL_KEYWORDS)

    def retrieve(self, message: str, assessment_type: str | None = None) -> Dict[str, Any]:
        collections = self._collections(assessment_type or "", message)
        queries = self._queries(message)
        trace = self.retrieval.retrieve(queries, collections, top_k=5)
        trace_dict = trace.model_dump(mode="json")
        return {
            "rag_used": bool(trace.retrieval_attempted),
            "real_legal_retrieval_used": bool(trace.real_legal_retrieval_used),
            "retrieval_fallback_used": bool(trace.retrieval_fallback_used or trace.fallback_used),
            "fallback_reason": trace.fallback_reason,
            "trace": trace_dict,
            "context_items": [item.model_dump(mode="json") for item in trace.items[:8]],
        }

    def _queries(self, message: str) -> List[str]:
        base = message.strip()[:240]
        if "出境" in message or "跨境" in message:
            return [base, "数据出境 安全评估 个人信息 出境 标准合同"]
        if "交易" in message or "流通" in message:
            return [base, "数据交易 数据流通 个人信息 合规 交易规则"]
        return [base]

    def _collections(self, assessment_type: str, message: str) -> List[str]:
        text = f"{assessment_type} {message}"
        if "cross_border" in text or "出境" in text or "跨境" in text:
            return ["cross_border_data_transfer", "personal_information", "important_data"]
        if "data_transaction" in text or "交易" in text or "流通" in text:
            return ["data_transaction", "personal_information", "cross_border_data_transfer"]
        if "pipl" in text.lower() or "个人信息" in text:
            return ["personal_information", "important_data"]
        return ["data_transaction", "personal_information", "cross_border_data_transfer"]
