from __future__ import annotations

from typing import List
from uuid import uuid4

from app.models.job import RuntimeEvent
from app.services.runtime_storage import RuntimeStorage
from app.services.storage_utils import append_jsonl, read_jsonl


class RuntimeEventService:
    def __init__(self) -> None:
        self.storage = RuntimeStorage()

    def add_event(self, job_id: str, event_type: str, stage: str, message: str, payload: dict | None = None) -> RuntimeEvent:
        event = RuntimeEvent(
            event_id=f"evt_{uuid4().hex}",
            job_id=job_id,
            event_type=event_type,
            stage=stage,
            message=message,
            payload=payload or {},
        )
        append_jsonl(self.storage.events_jsonl(job_id), event)
        return event

    def list_events(self, job_id: str) -> List[RuntimeEvent]:
        return [RuntimeEvent.model_validate(row) for row in read_jsonl(self.storage.events_jsonl(job_id))]
