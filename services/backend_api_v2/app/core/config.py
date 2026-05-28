from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime settings loaded from environment variables.

    This intentionally avoids pydantic-settings to keep dependencies small.
    """

    project_root: Path = Field(default_factory=lambda: Path(os.getenv("REGUTHINK_PROJECT_ROOT", Path.cwd())))
    full18_run_root: str = Field(
        default_factory=lambda: os.getenv(
            "REGUTHINK_FULL18_RUN_ROOT",
            "case_validation_v12/runs/phase11_1_full18_prototype_weighted_scoring_repair_20260518T121929Z",
        )
    )
    enable_runtime: bool = Field(default_factory=lambda: os.getenv("REGUTHINK_API_ENABLE_RUNTIME", "0") == "1")
    runtime_mode: str = Field(default_factory=lambda: os.getenv("REGUTHINK_API_RUNTIME_MODE", "disabled"))
    enable_real_autojudge: bool = Field(default_factory=lambda: os.getenv("REGUTHINK_API_ENABLE_REAL_AUTOJUDGE", "0") == "1")
    allow_uploaded_material_runtime: bool = Field(
        default_factory=lambda: os.getenv("REGUTHINK_API_ALLOW_UPLOADED_MATERIAL_RUNTIME", "0") == "1"
    )
    cors_origins: List[str] = Field(default_factory=list)
    runtime_storage_root: str = Field(
        default_factory=lambda: os.getenv("REGUTHINK_RUNTIME_STORAGE_ROOT", "runtime_storage")
    )
    upload_max_size_bytes: int = Field(
        default_factory=lambda: int(os.getenv("REGUTHINK_UPLOAD_MAX_SIZE_BYTES", str(25 * 1024 * 1024)))
    )
    upload_max_filename_length: int = Field(
        default_factory=lambda: int(os.getenv("REGUTHINK_UPLOAD_MAX_FILENAME_LENGTH", "120"))
    )
    upload_allowed_extensions: List[str] = Field(
        default_factory=lambda: [
            item.strip().lower()
            for item in os.getenv("REGUTHINK_UPLOAD_ALLOWED_EXTENSIONS", ".txt,.md,.json,.csv,.pdf,.docx,.xlsx").split(",")
            if item.strip()
        ]
    )

    phase: str = "Phase12-BE2-InteractiveChatFileUploadRuntimeBackend"
    baseline_phase: str = "Phase11.3"
    authoritative_validation_phase: str = "Phase11.2"
    interactive_backend_enabled: bool = True
    conversation_api_enabled: bool = True
    file_upload_enabled: bool = True
    sse_stream_enabled: bool = True
    assessment_types_enabled: bool = True
    dry_run_assessment_available: bool = True
    controlled_runtime_available: bool = Field(
        default_factory=lambda: os.getenv("REGUTHINK_API_ENABLE_RUNTIME", "0") == "1"
        and os.getenv("REGUTHINK_API_RUNTIME_MODE", "disabled") == "controlled"
    )
    real_multi_agent_runtime_enabled: bool = Field(
        default_factory=lambda: os.getenv("REGUTHINK_API_ENABLE_RUNTIME", "0") == "1"
        and os.getenv("REGUTHINK_API_RUNTIME_MODE", "disabled") == "controlled"
    )
    real_multi_agent_runtime_adapter_status: str = Field(
        default_factory=lambda: "partially_connected"
        if os.getenv("REGUTHINK_API_ENABLE_RUNTIME", "0") == "1"
        and os.getenv("REGUTHINK_API_RUNTIME_MODE", "disabled") == "controlled"
        else "not_configured_or_disabled"
    )

    @classmethod
    def from_env(cls) -> "Settings":
        origins = os.getenv(
            "REGUTHINK_API_CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173",
        )
        return cls(cors_origins=[item.strip() for item in origins.split(",") if item.strip()])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
