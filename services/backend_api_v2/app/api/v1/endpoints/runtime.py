from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.runtime_adapter import RuntimeAdapter

router = APIRouter()
adapter = RuntimeAdapter()


class RunCaseRequest(BaseModel):
    case_id: str
    dry_run: bool = True
    runtime_profile: Optional[str] = None


@router.post("/run-case")
def run_case(req: RunCaseRequest) -> dict:
    return adapter.run_case(case_id=req.case_id, dry_run=req.dry_run, runtime_profile=req.runtime_profile)
