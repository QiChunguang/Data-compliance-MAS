from __future__ import annotations

from pathlib import PurePath

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.runtime_event_service import RuntimeEventService
from app.services.runtime_job_service import RuntimeJobService

router = APIRouter()
job_service = RuntimeJobService()
event_service = RuntimeEventService()


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    try:
        return job_service.require_job(job_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/jobs/{job_id}/events")
def get_events(job_id: str) -> dict:
    try:
        job_service.require_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"events": [item.model_dump(mode="json") for item in event_service.list_events(job_id)]}


@router.get("/jobs/{job_id}/artifacts")
def get_artifacts(job_id: str) -> dict:
    try:
        return job_service.artifacts(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/jobs/{job_id}/artifacts/{artifact_name}/download")
def download_artifact(job_id: str, artifact_name: str):
    try:
        job_service.require_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if PurePath(artifact_name).name != artifact_name or artifact_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid artifact name.")
    root = job_service.storage.artifacts_dir(job_id).resolve()
    target = (root / artifact_name).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail=f"Unknown artifact: {artifact_name}")
    return FileResponse(
        target,
        filename=artifact_name,
        media_type="text/markdown" if artifact_name.endswith(".md") else "application/octet-stream",
    )


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    try:
        return job_service.cancel(job_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
