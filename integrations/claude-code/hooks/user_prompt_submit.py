#!/usr/bin/env python3
"""UserPromptSubmit hook: inject prompt-relevant lessons; off if TESSERA_RECALL_ON_PROMPT=0."""

from __future__ import annotations

import os
import sys

import _hooklib as hooklib


def main() -> int:
    if os.environ.get("TESSERA_RECALL_ON_PROMPT", "1") == "0":
        return 0
    event = hooklib.read_event()
    prompt = event.get("prompt", "")
    repo = hooklib.repo_id_from_cwd(event.get("cwd"))
    if not prompt.strip():
        return 0
    try:
        client = hooklib.make_client()
        resp = client.procedures.recall(task=prompt, user_id=repo)
    except Exception as exc:
        # Log only the type, not str(exc): SDK exceptions can carry the httpx.Request,
        # incl. the Authorization header.
        sys.stderr.write(f"tessera user_prompt_submit hook skipped: {type(exc).__name__}\n")
        return 0
    if not resp.results:
        return 0
    lines = [f"- {r.procedure.trigger}: {'; '.join(r.procedure.steps)}" for r in resp.results]
    context = "## Relevant Tessera lessons\n\n" + "\n".join(lines)
    hooklib.emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
