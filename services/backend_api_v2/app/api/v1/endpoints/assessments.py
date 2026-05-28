from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.job import RunAssessmentRequest
from app.services.assessment_router_service import AssessmentRouterService
from app.services.runtime_job_service import RuntimeJobService

router = APIRouter()
assessment_service = AssessmentRouterService()
job_service = RuntimeJobService()


@router.get("/assessment-types")
def assessment_types() -> dict:
    return {"assessment_types": [item.model_dump(mode="json") for item in assessment_service.list_types()]}


@router.post("/conversations/{conversation_id}/assessments/run")
def run_assessment(conversation_id: str, req: RunAssessmentRequest) -> dict:
    try:
        job = job_service.create_and_run(conversation_id, req)
        return {"job_id": job.job_id, "status": job.status, "message": "Assessment job created."}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
