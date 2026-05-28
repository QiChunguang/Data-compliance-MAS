from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.chat import utc_now


class UploadedFile(BaseModel):
    file_id: str
    conversation_id: str
    original_filename: str
    stored_path: str
    display_path: str
    mime_type: Optional[str] = None
    size_bytes: int
    sha256: str
    uploaded_at: str = utc_now()
    parse_status: str
    text_preview: Optional[str] = None
    extraction_warning: Optional[str] = None


class UploadFileResponse(BaseModel):
    file: UploadedFile
