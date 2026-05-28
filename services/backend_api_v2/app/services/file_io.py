from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


def read_text_if_exists(path: Path, max_chars: Optional[int] = None) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n\n[TRUNCATED]"
    return text


def read_json_if_exists(path: Path) -> Optional[Any]:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:  # intentionally defensive for artifact browsing
        return {"_parse_error": str(exc), "_path": str(path)}


def file_status(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }
