"""Read-only INDEX, diagnostic, scan, and check presentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import check_archive, render_index_bytes, schema_state, strict_json_bytes


def render_index(manifest: dict[str, Any]) -> bytes:
    return render_index_bytes(manifest)


def check_view(root: Path) -> dict[str, Any]:
    diagnostics = check_archive(Path(root))
    return {
        "path": str(root),
        "state": "valid" if not diagnostics else schema_state(Path(root))[0],
        "valid": not diagnostics,
        "diagnostics": diagnostics,
    }


def scan(done_root: Path) -> list[dict[str, Any]]:
    root = Path(done_root)
    if not root.is_dir():
        return [{
            "slug": None, "state": "missing", "reason": "done-root-missing",
            "next_action": "Pass an existing canonical done root.",
        }]
    results = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        if not child.is_dir():
            continue
        state, reason = schema_state(child)
        action = {
            "valid": f"Open {child.name}/INDEX.md, then run check.",
            "missing": "Treat as legacy read-only; do not modify it in place.",
            "malformed": "Inspect manifest.json; do not classify it as legacy.",
            "unsupported": "Use a reader that supports this schema; do not downgrade it.",
            "invalid": "Run check and follow the first stable diagnostic.",
        }[state]
        results.append({"slug": child.name, "state": state, "reason": reason, "next_action": action})
    return results


def human_check(view: dict[str, Any]) -> str:
    if view["valid"]:
        return f"valid-v1: {view['path']}\nnext_action: open INDEX.md and follow Next Reads"
    lines = [f"{view['state']}: {view['path']}"]
    for item in view["diagnostics"]:
        lines.extend((
            f"code: {item['code']}", f"summary: {item['summary']}",
            f"path: {item['path']}", f"next_action: {item['next_action']}",
        ))
    return "\n".join(lines)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
