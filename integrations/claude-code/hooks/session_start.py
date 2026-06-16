#!/usr/bin/env python3
"""SessionStart hook: recall repo memory and inject it as additional context."""

from __future__ import annotations

import sys

import _hooklib as hooklib


def main() -> int:
    event = hooklib.read_event()
    repo = hooklib.repo_id_from_cwd(event.get("cwd"))
    try:
        client = hooklib.make_client()
        resp = client.query(
            query="repo conventions, decisions, and recent work",
            mode="chat",
            user_id=repo,
        )
        context = hooklib.session_start_context(resp.context or "")
    except Exception as exc:
        # Never block the session on memory failure. Log only the type, not str(exc):
        # SDK exceptions can carry the httpx.Request, incl. the Authorization header.
        sys.stderr.write(f"tessera session_start hook skipped: {type(exc).__name__}\n")
        return 0
    if context:
        hooklib.emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            }
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
