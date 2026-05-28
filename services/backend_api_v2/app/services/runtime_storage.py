from __future__ import annotations

from pathlib import Path

from app.core.project_paths import get_project_paths


class RuntimeStorage:
    def __init__(self) -> None:
        self.root = get_project_paths().runtime_storage_root

    def ensure(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        gitignore = self.root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("*\n!.gitignore\n", encoding="utf-8")
        (self.root / "conversations").mkdir(parents=True, exist_ok=True)
        (self.root / "conversation_memory").mkdir(parents=True, exist_ok=True)
        (self.root / "uploads").mkdir(parents=True, exist_ok=True)
        (self.root / "jobs").mkdir(parents=True, exist_ok=True)
        return self.root

    @property
    def conversations_jsonl(self) -> Path:
        return self.ensure() / "conversations" / "conversations.jsonl"

    @property
    def messages_jsonl(self) -> Path:
        return self.ensure() / "conversations" / "messages.jsonl"

    def upload_dir(self, conversation_id: str) -> Path:
        path = self.ensure() / "uploads" / conversation_id
        (path / "files").mkdir(parents=True, exist_ok=True)
        return path

    def upload_manifest(self, conversation_id: str) -> Path:
        return self.upload_dir(conversation_id) / "manifest.json"

    def conversation_memory_dir(self, conversation_id: str) -> Path:
        safe_id = conversation_id.replace("\\", "_").replace("/", "_").replace("..", "_")
        path = self.ensure() / "conversation_memory" / safe_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def conversation_memory_messages(self, conversation_id: str) -> Path:
        return self.conversation_memory_dir(conversation_id) / "messages.jsonl"

    def conversation_memory_summary(self, conversation_id: str) -> Path:
        return self.conversation_memory_dir(conversation_id) / "memory_summary.json"

    def conversation_memory_summary_md(self, conversation_id: str) -> Path:
        return self.conversation_memory_dir(conversation_id) / "memory_summary.md"

    def conversation_memory_uploaded_files_index(self, conversation_id: str) -> Path:
        return self.conversation_memory_dir(conversation_id) / "uploaded_files_index.json"

    def conversation_memory_context_pack(self, conversation_id: str) -> Path:
        return self.conversation_memory_dir(conversation_id) / "latest_context_pack.json"

    def job_dir(self, job_id: str) -> Path:
        path = self.ensure() / "jobs" / job_id
        (path / "artifacts").mkdir(parents=True, exist_ok=True)
        return path

    def job_json(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "job.json"

    def events_jsonl(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "events.jsonl"

    def artifacts_dir(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "artifacts"

    def display_path(self, path: Path) -> str:
        return path.relative_to(self.ensure()).as_posix()
