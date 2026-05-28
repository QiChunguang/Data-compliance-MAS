from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple


TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv"}
PREVIEW_UNSUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}


class DocumentTextExtractor:
    def preview(self, path: Path, extension: str, max_chars: int = 4000) -> Tuple[str, str | None, str]:
        extension = extension.lower()
        if extension in TEXT_EXTENSIONS:
            text = path.read_text(encoding="utf-8", errors="replace")
            if extension == ".json":
                try:
                    parsed = json.loads(text)
                    text = json.dumps(parsed, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            warning = "preview_truncated" if len(text) > max_chars else None
            return "parsed", text[:max_chars], warning
        if extension in PREVIEW_UNSUPPORTED_EXTENSIONS:
            return "preview_unsupported", None, f"{extension} accepted but preview extraction is unsupported in BE2."
        return "unsupported", None, f"{extension} is not supported."
