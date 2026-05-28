from fastapi import APIRouter

from app.services.baseline_service import BaselineService

router = APIRouter()
service = BaselineService()


@router.get("/status")
def baseline_status() -> dict:
    return service.status()


@router.get("/reports")
def baseline_reports() -> dict:
    return service.reports()
