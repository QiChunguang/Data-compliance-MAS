from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


FORBIDDEN_EVIDENCE_PATTERNS = [
    "$(@{",
    "$(.Count)",
    "System.Object[]",
    "@{action=",
    "}.conversation_id",
    "}.automatic_agents_total",
    "}.summary",
]


def sanitize_evidence_text(text: str) -> List[str]:
    hits = [pattern for pattern in FORBIDDEN_EVIDENCE_PATTERNS if pattern in text]
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
        hits.append("control_character")
    if re.search(r"@\{[^}\n]+=", text):
        hits.append("raw_object_dump")
    return sorted(set(hits))


class AuditEvidenceRenderer:
    """Render audit markdown from JSON-compatible status only."""

    def render_markdown(self, status: Dict[str, Any], *, title: str) -> str:
        lines = [
            f"# {title}",
            "",
            "## Status",
            "",
        ]
        for key in [
            "phase",
            "overall_status",
            "backend_functional_status",
            "frontend_product_status",
            "report_quality_status",
            "graph_ux_status",
            "audit_evidence_status",
            "validation_status",
        ]:
            if key in status:
                lines.append(f"- {key}: `{self._scalar(status[key])}`")

        evidence = status.get("evidence", {})
        if isinstance(evidence, dict):
            lines.extend(["", "## Evidence", ""])
            for key, value in evidence.items():
                lines.append(f"- {key}: `{self._scalar(value)}`")

        gates = status.get("hard_gates", {})
        if isinstance(gates, dict):
            lines.extend(["", "## Hard Gates", ""])
            for key, value in gates.items():
                lines.append(f"- {key}: `{self._scalar(value)}`")

        warnings = status.get("warnings", [])
        if isinstance(warnings, list) and warnings:
            lines.extend(["", "## Warnings", ""])
            for item in warnings:
                lines.append(f"- {self._scalar(item)}")

        rendered = "\n".join(lines) + "\n"
        hits = sanitize_evidence_text(rendered)
        if hits:
            raise ValueError(f"Forbidden audit evidence tokens: {hits}")
        return rendered

    def write_pair(self, status: Dict[str, Any], *, json_path: Path, md_path: Path, title: str) -> None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(self.render_markdown(status, title=title), encoding="utf-8")

    def scan_files(self, paths: Iterable[Path]) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for path in paths:
            if not path.exists() or not path.is_file():
                continue
            hits = sanitize_evidence_text(path.read_text(encoding="utf-8", errors="replace"))
            if hits:
                result[str(path)] = hits
        return result

    def _scalar(self, value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        return str(value)
