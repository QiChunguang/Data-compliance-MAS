from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.assessment import AssessmentType


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationStatus(StrEnum):
    active = "active"
    archived = "archived"


class MessageRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class Conversation(BaseModel):
    conversation_id: str
    title: str
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    assessment_type: AssessmentType = AssessmentType.general_data_compliance_diagnostic
    status: ConversationStatus = ConversationStatus.active
    message_count: int = 0
    file_count: int = 0


class Message(BaseModel):
    message_id: str
    conversation_id: str
    role: MessageRole = MessageRole.user
    content: str
    created_at: str = Field(default_factory=utc_now)
    attachments: List[str] = Field(default_factory=list)
    run_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    assessment_type: AssessmentType = AssessmentType.general_data_compliance_diagnostic


class CreateMessageRequest(BaseModel):
    content: str
    attachments: List[str] = Field(default_factory=list)
