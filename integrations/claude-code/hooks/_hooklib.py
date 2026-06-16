"""Shared helpers for Claude Code Tessera hooks (stdlib + tessera_memory only)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def read_event() -> dict[str, Any]:
    raw = sys.stdin.read()
    return json.loads(raw) if raw.strip() else {}


def repo_id_from_cwd(cwd: str | None) -> str:
    name = Path(cwd).name if cwd else "unknown"
    return f"repo:{name}"


def session_start_context(memory_text: str) -> str | None:
    if not memory_text.strip():
        return None
    return f"## Tessera memory for this repo\n\n{memory_text}"


def make_client():
    # Imported lazily so importing this module stays stdlib-only.
    from tessera_memory import Tessera

    return Tessera(
        api_key=os.environ.get("TESSERA_API_KEY"),
        base_url=os.environ.get("TESSERA_BASE_URL"),
    )


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload))
