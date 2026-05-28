from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.models.upload import UploadedFile
from app.services.conversation_service import ConversationService
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.document_text_extractor import DocumentTextExtractor
from app.services.runtime_storage import RuntimeStorage
from app.services.storage_utils import write_json_atomic


class UploadValidationError(ValueError):
    pass


class FileUploadService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = RuntimeStorage()
        self.conversations = ConversationService()
        self.memory = ConversationMemoryService()
        self.extractor = DocumentTextExtractor()

    def sanitize_filename(self, filename: str) -> str:
        name = filename.replace("\\", "/").split("/")[-1]
        name = re.sub(r"^[a-zA-Z]:", "", name)
        name = re.sub(r"[^\w.\-\u4e00-\u9fff ]+", "_", name, flags=re.UNICODE).strip(" .")
        if not name:
            name = "uploaded_file"
        if len(name) > self.settings.upload_max_filename_length:
            stem = Path(name).stem[: self.settings.upload_max_filename_length - len(Path(name).suffix) - 1]
            name = f"{stem}{Path(name).suffix}"
        return name

    def validate_filename(self, filename: str) -> str:
        sanitized = self.sanitize_filename(filename)
        extension = Path(sanitized).suffix.lower()
        if extension not in self.settings.upload_allowed_extensions:
            raise UploadValidationError(f"Extension not allowed: {extension or '[none]'}")
        if len(sanitized) > self.settings.upload_max_filename_length:
            raise UploadValidationError("Filename too long after sanitization.")
        return sanitized

    async def save_upload(self, conversation_id: str, upload: UploadFile) -> UploadedFile:
        self.conversations.require_conversation(conversation_id)
        original_filename = upload.filename or "uploaded_file"
        safe_name = self.validate_filename(original_filename)
        content = await upload.read()
        size = len(content)
        if size == 0:
            raise UploadValidationError("Empty files are not allowed.")
        if size > self.settings.upload_max_size_bytes:
            raise UploadValidationError("File exceeds max upload size.")

        file_id = f"file_{uuid4().hex}"
        extension = Path(safe_name).suffix.lower()
        stored_name = f"{file_id}_{safe_name}"
        files_dir = self.storage.upload_dir(conversation_id) / "files"
        stored_abs = files_dir / stored_name
        stored_abs.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        parse_status, preview, warning = self.extractor.preview(stored_abs, extension)
        display_path = self.storage.display_path(stored_abs)
        record = UploadedFile(
            file_id=file_id,
            conversation_id=conversation_id,
            original_filename=original_filename,
            stored_path=display_path,
            display_path=display_path,
            mime_type=upload.content_type,
            size_bytes=size,
            sha256=digest,
            parse_status=parse_status,
            text_preview=preview,
            extraction_warning=warning,
        )
        self._append_manifest(conversation_id, record)
        self.memory.record_uploaded_file(record)
        self.conversations.increment_file_count(conversation_id)
        return record

    def list_files(self, conversation_id: str) -> List[UploadedFile]:
        manifest = self._read_manifest(conversation_id)
        return [UploadedFile.model_validate(item) for item in manifest]

    def get_file(self, file_id: str) -> UploadedFile | None:
        uploads_root = self.storage.ensure() / "uploads"
        for manifest_path in uploads_root.glob("*/manifest.json"):
            items = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
            for item in items:
                if item.get("file_id") == file_id:
                    return UploadedFile.model_validate(item)
        return None

    def _read_manifest(self, conversation_id: str) -> List[dict]:
        path = self.storage.upload_manifest(conversation_id)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _append_manifest(self, conversation_id: str, record: UploadedFile) -> None:
        manifest = self._read_manifest(conversation_id)
        manifest.append(record.model_dump(mode="json"))
        write_json_atomic(self.storage.upload_manifest(conversation_id), manifest)
