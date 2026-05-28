from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

from app.services.llm_config_service import LLMConfigService

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


class LLMChatService:
    def __init__(self) -> None:
        self.config = LLMConfigService()

    def complete(
        self,
        *,
        user_message: str,
        intent: str,
        rag_context: List[Dict[str, Any]] | None = None,
        uploaded_context: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        summary = self.config.summary()
        if not summary.get("key_present"):
            return self._unavailable("agent LLM API key missing", summary)

        try:
            from core.config import CURRENT_PLATFORM, LLM_TIMEOUT, PLATFORM_CONFIGS
            from core.llm_boundary_guard import guarded_completion_call
            from core.utils import get_llm_client

            cfg = PLATFORM_CONFIGS.get(CURRENT_PLATFORM)
            if cfg is None or not cfg.api_key:
                return self._unavailable("agent LLM platform is not configured", summary)

            messages = [
                {"role": "system", "content": self._system_prompt(intent)},
                {"role": "user", "content": self._user_prompt(user_message, rag_context or [], uploaded_context or [])},
            ]

            client = get_llm_client(timeout=LLM_TIMEOUT)
            boundary_result = guarded_completion_call(
                boundary_id="be7_conversational_chat_completion",
                call_fn=lambda: client.chat.completions.create(
                    model=cfg.model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=1200,
                ),
                input_summary={
                    "intent": intent,
                    "user_message_chars": len(user_message),
                    "rag_items": len(rag_context or []),
                    "uploaded_context_items": len(uploaded_context or []),
                },
                node_name="be7_conversational_chat",
            )
            if boundary_result.degraded:
                return self._unavailable(f"LLM boundary degraded: {boundary_result.reason}", summary)
            response = boundary_result.value
            content = (response.choices[0].message.content or "").strip()
            if not content:
                return self._unavailable("LLM returned empty content", summary)
            return {
                "llm_used": True,
                "llm_unavailable": False,
                "content": content,
                "llm_config": summary,
            }
        except Exception as exc:
            return self._unavailable(f"{type(exc).__name__}: {exc}", summary)

    def _system_prompt(self, intent: str) -> str:
        return (
            "你是 ReguThink 数据合规智能体。请用自然、清晰的中文回答，像专业助手而不是报告模板。\n"
            "边界要求：不构成正式法律意见；上传材料只能作为业务事实，不是法律依据；"
            "法律依据只能来自只读法规库/RAG 摘要或明确的一般性说明；不要编造法规条文、source_backed、manual_verified 或 article_level_verified。\n"
            "如果用户需要完整审查报告，请提示其上传业务材料并点击“生成审查报告”。\n"
            f"当前意图：{intent}"
        )

    def _user_prompt(
        self,
        user_message: str,
        rag_context: List[Dict[str, Any]],
        uploaded_context: List[Dict[str, Any]],
    ) -> str:
        rag_lines = []
        for item in rag_context[:8]:
            rag_lines.append(
                f"- source_id={item.get('source_id','')}; chunk_id={item.get('chunk_id','')}; "
                f"collection={item.get('collection','')}; role={item.get('evidence_role','')}; "
                f"fallback={item.get('fallback_used', True)}"
            )
        upload_lines = []
        for item in uploaded_context[:6]:
            preview = str(item.get("text_preview") or "")[:1200]
            upload_lines.append(
                f"- file_id={item.get('file_id','')}; filename={item.get('original_filename','')}; "
                f"parse_status={item.get('parse_status','')}; preview={preview}"
            )
        return (
            f"用户问题：\n{user_message}\n\n"
            "只读法规/RAG 摘要（可能为空；fallback=true 时只能作为有限参考，不得包装成真实法规命中）：\n"
            + ("\n".join(rag_lines) if rag_lines else "无可用 RAG 摘要")
            + "\n\n上传材料业务事实摘要（可能为空；不是法律依据）：\n"
            + ("\n".join(upload_lines) if upload_lines else "无上传材料上下文")
            + "\n\n请直接回答用户问题。"
        )

    def _unavailable(self, reason: str, summary: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "llm_used": False,
            "llm_unavailable": True,
            "unavailable_reason": reason,
            "llm_config": summary,
            "content": (
                "LLM 当前不可用，无法生成自然语言智能体回答。"
                "我不会使用固定 Prototype Diagnostic 模板冒充大模型结果。"
                f"不可用原因：{reason}"
            ),
        }
