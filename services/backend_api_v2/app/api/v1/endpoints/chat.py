from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.chat_orchestrator_service import ChatOrchestratorService, ChatRequest

router = APIRouter()
service = ChatOrchestratorService()


@router.post("/{conversation_id}/chat")
def chat(conversation_id: str, req: ChatRequest) -> dict:
    try:
        response = service.chat(conversation_id, req)
        return response.model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc