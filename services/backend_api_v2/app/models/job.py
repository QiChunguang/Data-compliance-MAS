from __future__ import annotations

from enum import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.assessment import AssessmentType
from app.models.chat import utc_now


class RuntimeMode(StrEnum):
    chat = "chat"
    dry_run = "dry_run"
    controlled_runtime = "controlled_runtime"
    uploaded_material_runtime = "uploaded_material_runtime"
    full_chain_runtime = "full_chain_runtime"


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class RuntimeJob(BaseModel):
    job_id: str
    conversation_id: str
    assessment_type: AssessmentType
    status: JobStatus = JobStatus.queued
    created_at: str = Field(default_factory=utc_now)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0
    current_stage: str = "queued"
    input_files: List[str] = Field(default_factory=list)
    user_prompt: str = ""
    result_artifacts: Dict[str, str] = Field(default_factory=dict)
    error_message: Optional[str] = None
    boundary_flags: Dict[str, Any] = Field(default_factory=dict)
    runtime_mode: RuntimeMode = RuntimeMode.dry_run


class RuntimeEvent(BaseModel):
    event_id: str
    job_id: str
    event_type: str
    stage: str
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


class RunAssessmentRequest(BaseModel):
    assessment_type: AssessmentType
    user_prompt: str
    file_ids: List[str] = Field(default_factory=list)
    runtime_mode: RuntimeMode = RuntimeMode.dry_run
    action: str = "run_assessment"
    autojudge_enabled: bool = True


class RunAssessmentResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    job: RuntimeJob


class JobEventsResponse(BaseModel):
    events: List[RuntimeEvent]
