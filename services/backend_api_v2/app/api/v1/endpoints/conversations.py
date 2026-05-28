from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.chat import CreateConversationRequest, CreateMessageRequest
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.conversation_service import ConversationService
from app.services.runtime_job_service import RuntimeJobService

router = APIRouter()
service = ConversationService()
job_service = RuntimeJobService()
memory_service = ConversationMemoryService()


@router.post("")
def create_conversation(req: CreateConversationRequest) -> dict:
    return service.create_conversation(req).model_dump(mode="json")


@router.get("")
def list_conversations() -> dict:
    return {"conversations": [item.model_dump(mode="json") for item in service.list_conversations()]}


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str) -> dict:
    conversation = service.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail=f"Unknown conversation_id: {conversation_id}")
    return conversation.model_dump(mode="json")


@router.get("/{conversation_id}/messages")
def list_messages(conversation_id: str) -> dict:
    try:
        service.require_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"messages": [item.model_dump(mode="json") for item in service.list_messages(conversation_id)]}


@router.get("/{conversation_id}/latest-job")
def latest_job(conversation_id: str) -> dict:
    try:
        service.require_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    job = job_service.latest_for_conversation(conversation_id)
    return {"job": job.model_dump(mode="json") if job else None}


@router.get("/{conversation_id}/jobs")
def list_jobs(conversation_id: str) -> dict:
    try:
        service.require_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"jobs": [item.model_dump(mode="json") for item in job_service.list_for_conversation(conversation_id)]}


@router.get("/{conversation_id}/memory")
def get_memory(conversation_id: str) -> dict:
    try:
        service.require_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return memory_service.get_memory(conversation_id)


@router.post("/{conversation_id}/messages")
def create_message(conversation_id: str, req: CreateMessageRequest) -> dict:
    try:
        return service.add_message(conversation_id, req).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
