from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from app.models.chat import Message
from app.models.job import RuntimeJob
from app.services.runtime_storage import RuntimeStorage
from app.services.storage_utils import append_jsonl, read_jsonl, write_json_atomic


class ConversationMemoryService:
    """Per-conversation local memory with bounded, non-secret summaries."""

    SECRET_MARKERS = ("api_key", "apikey", "secret", "password", "token", "neo4j")

    def __init__(self) -> None:
        self.storage = RuntimeStorage()

    def initialize_conversation(self, conversation_id: str) -> None:
        self.storage.conversation_memory_dir(conversation_id)
        messages = self.storage.conversation_memory_messages(conversation_id)
        if not messages.exists():
            messages.write_text("", encoding="utf-8")
        if not self.storage.conversation_memory_uploaded_files_index(conversation_id).exists():
            write_json_atomic(self.storage.conversation_memory_uploaded_files_index(conversation_id), {
                "conversation_id": conversation_id,
                "files": [],
                "safety": {
                    "stores_absolute_paths": False,
                    "stores_uploaded_file_full_text": False,
                    "stores_api_keys_or_passwords": False,
                },
            })
        if not self.storage.conversation_memory_context_pack(conversation_id).exists():
            write_json_atomic(self.storage.conversation_memory_context_pack(conversation_id), {
                "conversation_id": conversation_id,
                "jobs": [],
                "recent_messages": [],
                "uploaded_files": [],
            })
        self.refresh_summary(conversation_id)

    def record_message(self, message: Message) -> None:
        self.initialize_conversation(message.conversation_id)
        row = {
            "message_id": message.message_id,
            "conversation_id": message.conversation_id,
            "role": str(message.role),
            "created_at": message.created_at,
            "attachments": list(message.attachments),
            "content_excerpt": self._scrub_text(message.content, limit=2000),
            "content_truncated": len(message.content or "") > 2000,
        }
        append_jsonl(self.storage.conversation_memory_messages(message.conversation_id), row)
        self.refresh_summary(message.conversation_id)

    def record_uploaded_file(self, file_record: Any) -> None:
        conversation_id = str(getattr(file_record, "conversation_id", ""))
        if not conversation_id:
            return
        self.initialize_conversation(conversation_id)
        index_path = self.storage.conversation_memory_uploaded_files_index(conversation_id)
        data = self._read_json(index_path)
        if not isinstance(data, dict):
            data = {"conversation_id": conversation_id, "files": []}
        files = [item for item in data.get("files", []) if item.get("file_id") != getattr(file_record, "file_id", "")]
        excerpt = self._scrub_text(str(getattr(file_record, "text_preview", "") or ""), limit=800)
        files.append({
            "file_id": getattr(file_record, "file_id", ""),
            "original_filename": self._scrub_text(str(getattr(file_record, "original_filename", "")), limit=160),
            "mime_type": getattr(file_record, "mime_type", None),
            "size_bytes": getattr(file_record, "size_bytes", 0),
            "parse_status": getattr(file_record, "parse_status", "unknown"),
            "display_path": str(getattr(file_record, "display_path", "")).replace("\\", "/"),
            "bounded_excerpt": excerpt,
            "excerpt_truncated": bool(getattr(file_record, "text_preview", "") and len(getattr(file_record, "text_preview", "")) > 800),
        })
        data["files"] = files[-30:]
        data["safety"] = {
            "stores_absolute_paths": False,
            "stores_uploaded_file_full_text": False,
            "stores_api_keys_or_passwords": False,
        }
        write_json_atomic(index_path, data)
        context = self._read_context(conversation_id)
        context["uploaded_files"] = [
            {
                "file_id": item.get("file_id"),
                "original_filename": item.get("original_filename"),
                "size_bytes": item.get("size_bytes"),
                "parse_status": item.get("parse_status"),
                "bounded_excerpt": item.get("bounded_excerpt"),
            }
            for item in data["files"][-10:]
        ]
        write_json_atomic(self.storage.conversation_memory_context_pack(conversation_id), context)
        self.refresh_summary(conversation_id)

    def record_job_summary(self, job: RuntimeJob, artifacts: Dict[str, str] | None = None) -> None:
        self.initialize_conversation(job.conversation_id)
        context = self._read_context(job.conversation_id)
        job_summary = {
            "job_id": job.job_id,
            "status": str(job.status),
            "runtime_mode": str(job.runtime_mode),
            "assessment_type": str(job.assessment_type),
            "completed_at": job.completed_at,
            "artifact_names": sorted((artifacts or job.result_artifacts or {}).keys()),
            "human_review_status": "not_reviewed",
            "autojudge_policy": "auto_on_for_report_generation",
        }
        jobs = [item for item in context.get("jobs", []) if item.get("job_id") != job.job_id]
        jobs.append(job_summary)
        context["jobs"] = jobs[-20:]
        write_json_atomic(self.storage.conversation_memory_context_pack(job.conversation_id), context)
        self.refresh_summary(job.conversation_id)

    def get_memory(self, conversation_id: str) -> Dict[str, Any]:
        memory_dir = self.storage.conversation_memory_dir(conversation_id)
        summary_path = self.storage.conversation_memory_summary(conversation_id)
        context_path = self.storage.conversation_memory_context_pack(conversation_id)
        return {
            "conversation_id": conversation_id,
            "memory_dir": self.storage.display_path(memory_dir),
            "messages_path": self.storage.display_path(self.storage.conversation_memory_messages(conversation_id)),
            "summary_md_path": self.storage.display_path(self.storage.conversation_memory_summary_md(conversation_id)),
            "uploaded_files_index_path": self.storage.display_path(self.storage.conversation_memory_uploaded_files_index(conversation_id)),
            "summary": self._read_json(summary_path),
            "latest_context_pack": self._read_json(context_path),
        }

    def refresh_summary(self, conversation_id: str) -> None:
        memory_dir = self.storage.conversation_memory_dir(conversation_id)
        messages_path = memory_dir / "messages.jsonl"
        if not messages_path.exists():
            messages_path.write_text("", encoding="utf-8")
        rows = read_jsonl(self.storage.conversation_memory_messages(conversation_id))
        counts = Counter(str(row.get("role", "unknown")) for row in rows)
        recent = rows[-8:]
        keywords = self._keywords(recent)
        uploaded_index = self._read_json(self.storage.conversation_memory_uploaded_files_index(conversation_id))
        uploaded_files = uploaded_index.get("files", []) if isinstance(uploaded_index, dict) else []
        summary = {
            "conversation_id": conversation_id,
            "message_count": len(rows),
            "role_counts": dict(counts),
            "recent_message_ids": [row.get("message_id") for row in recent],
            "topic_keywords": keywords,
            "uploaded_file_count": len(uploaded_files),
            "safety": {
                "stores_absolute_paths": False,
                "stores_uploaded_file_full_text": False,
                "stores_api_keys_or_passwords": False,
            },
        }
        write_json_atomic(self.storage.conversation_memory_summary(conversation_id), summary)
        md_lines = [
            f"# Conversation Memory Summary",
            "",
            f"- conversation_id: {conversation_id}",
            f"- message_count: {len(rows)}",
            f"- uploaded_file_count: {len(uploaded_files)}",
            f"- topic_keywords: {', '.join(keywords) if keywords else 'none'}",
            "- safety: no secrets, no absolute paths, no uploaded full text",
            "",
        ]
        self.storage.conversation_memory_summary_md(conversation_id).write_text("\n".join(md_lines), encoding="utf-8")
        context = self._read_context(conversation_id)
        context.update({
            "conversation_id": conversation_id,
            "recent_messages": [
                {
                    "message_id": row.get("message_id"),
                    "role": row.get("role"),
                    "content_excerpt": self._scrub_text(str(row.get("content_excerpt", "")), limit=600),
                    "attachments": row.get("attachments", []),
                }
                for row in recent
            ],
            "topic_keywords": keywords,
        })
        write_json_atomic(self.storage.conversation_memory_context_pack(conversation_id), context)

    def _read_context(self, conversation_id: str) -> Dict[str, Any]:
        data = self._read_json(self.storage.conversation_memory_context_pack(conversation_id))
        return data if isinstance(data, dict) else {"conversation_id": conversation_id, "jobs": []}

    def _read_json(self, path) -> Any:
        if not path.exists():
            return {}
        try:
            import json

            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _scrub_text(self, text: str, *, limit: int) -> str:
        cleaned_lines: List[str] = []
        for line in (text or "").replace("\\", "/").splitlines():
            lower = line.lower()
            if any(marker in lower for marker in self.SECRET_MARKERS):
                cleaned_lines.append("[redacted]")
                continue
            if ":/" in line or line.startswith("//"):
                cleaned_lines.append("[path_redacted]")
                continue
            cleaned_lines.append(line[:limit])
        return "\n".join(cleaned_lines)[:limit]

    def _keywords(self, rows: List[Dict[str, Any]]) -> List[str]:
        text = " ".join(str(row.get("content_excerpt", "")) for row in rows)
        candidates = ["上传", "材料", "审查报告", "合规", "个人信息", "数据交易", "跨境", "AutoJudge", "人工复核"]
        return [item for item in candidates if item.lower() in text.lower()][:8]
