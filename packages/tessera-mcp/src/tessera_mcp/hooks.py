"""Claude Code hooks, run via ``tessera-mcp hook <event>``.

Hooks run inside the uvx-managed environment that already has the SDK, so they never depend
on whatever ``python3`` happens to be on PATH (the bug that made them silently no-op). They
read the hook event JSON on stdin and emit ``additionalContext`` on stdout.

The repo identity is auto-detected from the event's ``cwd`` (same logic as the server), and
the API key comes from the shared credential store. Every hook fails open: any error is
swallowed so memory never blocks a session.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from .credentials import load_api_key
from .repo import detect_repo_id

# --- shared helpers ---------------------------------------------------------------------


def _read_event() -> dict[str, Any]:
    raw = sys.stdin.read()
    return json.loads(raw) if raw.strip() else {}


def _repo(event: dict[str, Any]) -> str:
    return detect_repo_id(event.get("cwd"))


def _make_client() -> Any:
    # Imported lazily so the module import stays cheap for the hook dispatcher.
    from tessera_memory import Tessera

    return Tessera(api_key=load_api_key(), base_url=os.environ.get("TESSERA_BASE_URL"))


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload))


def session_start_context(memory_text: str) -> str | None:
    if not memory_text.strip():
        return None
    return f"## Tessera memory for this repo\n\n{memory_text}"


# --- session_start ----------------------------------------------------------------------


def session_start() -> int:
    """Recall repo memory and inject it as additional context."""
    if not load_api_key():
        return 0
    event = _read_event()
    repo = _repo(event)
    try:
        resp = _make_client().query(
            query="repo conventions, decisions, and recent work",
            mode="chat",
            user_id=repo,
        )
        context = session_start_context(resp.context or "")
    except Exception as exc:
        # Never block the session on memory failure. Log only the type, not str(exc):
        # SDK exceptions can carry the httpx.Request, incl. the Authorization header.
        sys.stderr.write(f"tessera session_start hook skipped: {type(exc).__name__}\n")
        return 0
    if context:
        _emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            }
        )
    return 0


# --- user_prompt_submit -----------------------------------------------------------------


def user_prompt_submit() -> int:
    """Inject prompt-relevant lessons; off if TESSERA_RECALL_ON_PROMPT=0."""
    if os.environ.get("TESSERA_RECALL_ON_PROMPT", "1") == "0":
        return 0
    if not load_api_key():
        return 0
    event = _read_event()
    prompt = event.get("prompt", "")
    repo = _repo(event)
    if not prompt.strip():
        return 0
    try:
        resp = _make_client().procedures.recall(task=prompt, user_id=repo)
    except Exception as exc:
        # Log only the type, not str(exc): SDK exceptions can carry the httpx.Request,
        # incl. the Authorization header.
        sys.stderr.write(f"tessera user_prompt_submit hook skipped: {type(exc).__name__}\n")
        return 0
    if not resp.results:
        return 0
    lines = [f"- {r.procedure.trigger}: {'; '.join(r.procedure.steps)}" for r in resp.results]
    context = "## Relevant Tessera lessons\n\n" + "\n".join(lines)
    _emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }
    )
    return 0


# --- session_end ------------------------------------------------------------------------

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


def session_end() -> int:
    """Ship the redacted transcript; opt-in via TESSERA_CONSOLIDATE_TRANSCRIPT=1."""
    if os.environ.get("TESSERA_CONSOLIDATE_TRANSCRIPT", "0") != "1":
        return 0
    if not load_api_key():
        return 0
    event = _read_event()
    repo = _repo(event)
    session = event.get("session_id")
    messages = _load_transcript(event.get("transcript_path"))
    if not messages:
        return 0
    try:
        _make_client().memories.batch(messages=messages, user_id=repo, session_id=session)
    except Exception as exc:
        # Log only the type, not str(exc): SDK exceptions can carry the httpx.Request,
        # incl. the Authorization header.
        sys.stderr.write(f"tessera session_end hook skipped: {type(exc).__name__}\n")
    return 0


# --- dispatch ---------------------------------------------------------------------------

_EVENTS = {
    "session-start": session_start,
    "user-prompt-submit": user_prompt_submit,
    "session-end": session_end,
}


def run(event: str) -> int:
    handler = _EVENTS.get(event)
    if handler is None:
        sys.stderr.write(f"tessera: unknown hook event {event!r}\n")
        return 0
    return handler()
