from fastapi import APIRouter, HTTPException

from app.services.case_service import CaseService

router = APIRouter()
service = CaseService()


@router.get("")
def list_cases() -> dict:
    rows = service.list_cases()
    return {
        "case_count": len(rows),
        "case_count_score_ge_70": sum(1 for row in rows if row["ge_70"]),
        "cases": rows,
        "warning": "Diagnostic prototype scores only; not legal opinions.",
    }


@router.get("/{case_id}")
def get_case(case_id: str) -> dict:
    row = service.get_case(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown case_id: {case_id}")
    return row
