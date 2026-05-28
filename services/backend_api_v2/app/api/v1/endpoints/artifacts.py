from fastapi import APIRouter, HTTPException

from app.services.artifact_service import ArtifactService
from app.services.case_service import CaseService

router = APIRouter()
artifact_service = ArtifactService()
case_service = CaseService()


def ensure_case(case_id: str) -> None:
    if case_service.get_case(case_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown case_id: {case_id}")


@router.get("/{case_id}/artifacts")
def get_case_artifacts(case_id: str) -> dict:
    ensure_case(case_id)
    return artifact_service.artifact_bundle(case_id)


@router.get("/{case_id}/report")
def get_case_report(case_id: str) -> dict:
    ensure_case(case_id)
    return artifact_service.report(case_id)
