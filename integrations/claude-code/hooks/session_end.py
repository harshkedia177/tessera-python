#!/usr/bin/env python3
"""SessionEnd hook: ship the redacted transcript to Tessera for consolidation.

Opt-in via TESSERA_CONSOLIDATE_TRANSCRIPT=1 (uploading ships session text off the
machine). See CLAUDE.md.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import _hooklib as hooklib

# Conservative (over-redacting) patterns: transcripts routinely contain pasted keys,
# printed .env files, and credentials in command output.
_REDACTIONS: list[re.Pattern[str]] = [
    # KEY=/TOKEN=/SECRET=/PASSWORD=/PASSWD=/PWD= assignments (incl. `export X=...`).
    re.compile(
        r"(?im)\b([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|PWD)[A-Z0-9_]*)\s*[=:]\s*\S+"
    ),
    # Provider tokens: sk-..., tsk_..., gh[opsu]_..., xox[abprs]-..., AWS AKIA....
    re.compile(r"(?i)\b(sk-[A-Za-z0-9_-]{12,})"),
    re.compile(r"\b(tsk_[A-Za-z0-9_-]{8,})"),
    re.compile(r"\b(gh[opsu]_[A-Za-z0-9]{20,})"),
    re.compile(r"\b(xox[abprs]-[A-Za-z0-9-]{8,})"),
    re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
    re.compile(r"(?i)\bAuthorization\s*:\s*\S+\s+\S+"),
    re.compile(
        r"-----BEGIN[^-]*PRIVATE KEY-----.*?-----END[^-]*PRIVATE KEY-----",
        re.DOTALL,
    ),
]

_REDACTED = "[REDACTED]"


def _redact(text: str) -> str:
    for pat in _REDACTIONS:
        text = pat.sub(_REDACTED, text)
    return text


def _flatten_content(content: object) -> str:
    # content is a str (user turns) or a list of blocks; only text blocks contribute.
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            b["text"]
            for b in content
            if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
        ]
        return " ".join(p.strip() for p in parts if p.strip()).strip()
    return ""


def _load_transcript(path: str | None) -> list[dict[str, str]]:
    # Turn text lives under rec["message"]["content"]; the top-level "content" is None.
    if not path or not Path(path).exists():
        return []
    messages: list[dict[str, str]] = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        role = rec.get("type")
        if role not in ("user", "assistant"):
            continue
        msg = rec.get("message") or {}
        content = _flatten_content(msg.get("content"))
        if not content:
            continue
        messages.append({"role": role, "content": _redact(content)})
    return messages


def main() -> int:
    if os.environ.get("TESSERA_CONSOLIDATE_TRANSCRIPT", "0") != "1":
        return 0
    event = hooklib.read_event()
    repo = hooklib.repo_id_from_cwd(event.get("cwd"))
    session = event.get("session_id")
    messages = _load_transcript(event.get("transcript_path"))
    if not messages:
        return 0
    try:
        client = hooklib.make_client()
        client.memories.batch(messages=messages, user_id=repo, session_id=session)
    except Exception as exc:
        # Log only the type, not str(exc): SDK exceptions can carry the httpx.Request,
        # incl. the Authorization header.
        sys.stderr.write(f"tessera session_end hook skipped: {type(exc).__name__}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
