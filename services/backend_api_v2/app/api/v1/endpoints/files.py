from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.file_upload_service import FileUploadService, UploadValidationError

router = APIRouter()
service = FileUploadService()


@router.post("/conversations/{conversation_id}/files")
async def upload_file(conversation_id: str, file: UploadFile = File(...)) -> dict:
    try:
        uploaded = await service.save_upload(conversation_id, file)
        return uploaded.model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/conversations/{conversation_id}/files")
def list_files(conversation_id: str) -> dict:
    try:
        service.conversations.require_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"files": [item.model_dump(mode="json") for item in service.list_files(conversation_id)]}


@router.get("/files/{file_id}")
def get_file(file_id: str) -> dict:
    uploaded = service.get_file(file_id)
    if uploaded is None:
        raise HTTPException(status_code=404, detail=f"Unknown file_id: {file_id}")
    return uploaded.model_dump(mode="json")
