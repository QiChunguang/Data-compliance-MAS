from __future__ import annotations

import json
import time
from typing import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.job import JobStatus
from app.services.runtime_event_service import RuntimeEventService
from app.services.runtime_job_service import RuntimeJobService

router = APIRouter()
job_service = RuntimeJobService()
event_service = RuntimeEventService()


def sse_line(event_type: str, payload: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/jobs/{job_id}/stream")
def stream_job(job_id: str) -> StreamingResponse:
    try:
        job_service.require_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    def generate() -> Iterator[str]:
        sent = set()
        while True:
            job = job_service.require_job(job_id)
            for event in event_service.list_events(job_id):
                if event.event_id not in sent:
                    sent.add(event.event_id)
                    yield sse_line(event.event_type, event.model_dump(mode="json"))
            if job.status in {JobStatus.completed, JobStatus.failed, JobStatus.cancelled}:
                yield sse_line(
                    "final",
                    {
                        "job_id": job_id,
                        "status": job.status,
                        "message": f"Stream closed after terminal status: {job.status}",
                    },
                )
                break
            time.sleep(0.25)

    return StreamingResponse(generate(), media_type="text/event-stream")
