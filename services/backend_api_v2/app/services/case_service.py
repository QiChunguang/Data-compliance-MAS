from __future__ import annotations

from typing import Dict, List, Optional

from app.data.phase11_2_case_baseline import PHASE11_2_CASE_BASELINE


class CaseService:
    def list_cases(self) -> List[Dict]:
        return PHASE11_2_CASE_BASELINE

    def get_case(self, case_id: str) -> Optional[Dict]:
        return next((row for row in PHASE11_2_CASE_BASELINE if row["case_id"] == case_id), None)
