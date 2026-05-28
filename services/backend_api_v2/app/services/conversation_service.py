from __future__ import annotations

from typing import List
from uuid import uuid4

from app.models.chat import Conversation, CreateConversationRequest, CreateMessageRequest, Message, MessageRole, utc_now
from app.models.upload import UploadedFile
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.runtime_storage import RuntimeStorage
from app.services.storage_utils import append_jsonl, latest_by_id, read_jsonl


class ConversationService:
    def __init__(self) -> None:
        self.storage = RuntimeStorage()
        self.memory = ConversationMemoryService()

    def create_conversation(self, req: CreateConversationRequest) -> Conversation:
        title = req.title or "Untitled diagnostic conversation"
        conversation = Conversation(
            conversation_id=f"conv_{uuid4().hex}",
            title=title,
            assessment_type=req.assessment_type,
        )
        append_jsonl(self.storage.conversations_jsonl, conversation)
        self.memory.initialize_conversation(conversation.conversation_id)
        return conversation

    def list_conversations(self) -> List[Conversation]:
        rows = latest_by_id(read_jsonl(self.storage.conversations_jsonl), "conversation_id")
        return [Conversation.model_validate(row) for row in rows.values()]

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        rows = latest_by_id(read_jsonl(self.storage.conversations_jsonl), "conversation_id")
        row = rows.get(conversation_id)
        return Conversation.model_validate(row) if row else None

    def list_messages(self, conversation_id: str) -> List[Message]:
        return [
            Message.model_validate(row)
            for row in read_jsonl(self.storage.messages_jsonl)
            if row.get("conversation_id") == conversation_id
        ]

    def add_message(self, conversation_id: str, req: CreateMessageRequest, role: MessageRole = MessageRole.user) -> Message:
        conversation = self.require_conversation(conversation_id)
        message = Message(
            message_id=f"msg_{uuid4().hex}",
            conversation_id=conversation_id,
            role=role,
            content=req.content,
            attachments=req.attachments,
        )
        append_jsonl(self.storage.messages_jsonl, message)
        self.memory.record_message(message)
        updated = conversation.model_copy(
            update={
                "updated_at": utc_now(),
                "message_count": conversation.message_count + 1,
            }
        )
        append_jsonl(self.storage.conversations_jsonl, updated)
        return message

    def increment_file_count(self, conversation_id: str) -> None:
        conversation = self.require_conversation(conversation_id)
        updated = conversation.model_copy(
            update={
                "updated_at": utc_now(),
                "file_count": conversation.file_count + 1,
            }
        )
        append_jsonl(self.storage.conversations_jsonl, updated)

    def require_conversation(self, conversation_id: str) -> Conversation:
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            raise KeyError(f"Unknown conversation_id: {conversation_id}")
        return conversation
