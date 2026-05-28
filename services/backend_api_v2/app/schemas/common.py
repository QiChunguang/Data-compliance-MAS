from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BoundaryFlags(BaseModel):
    not_production_ready: bool = True
    not_source_backed_pass: bool = True
    not_human_reviewed: bool = True
    prototype_context: bool = True
    business_case_files_available: bool = False
    business_evidence_files_available: bool = False
    local_neural_reranker_default_enabled: bool = False
    local_neural_reranker_status: str = "diagnostic_only"
    bge_m3_status: str = "partially_effective"
    full18_mode: str = "mode_a_bgem3_authority_rerank"


class FileStatus(BaseModel):
    path: str
    exists: bool
    size_bytes: Optional[int] = None


class ApiEnvelope(BaseModel):
    ok: bool
    message: str
    boundary_flags: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
