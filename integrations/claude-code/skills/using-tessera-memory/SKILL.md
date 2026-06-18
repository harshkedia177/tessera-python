---
name: using-tessera-memory
description: Use when starting a coding task, when corrected by the user, or when you hit a gotcha — to recall prior decisions/conventions/lessons from Tessera memory and to save new ones so they are not lost across sessions.
---

# Using Tessera Memory

Tessera is this repo's long-term memory. Use the MCP tools deliberately. Memory is
isolated per git repo automatically — there is no repo name to set.

## First-run setup (only if a tool reports no key)
If a memory tool replies that no API key is configured, do this once:
1. Ask the user for their Tessera API key (it starts with `tsk_live_`).
2. Run `uvx --from tessera-mcp tessera-mcp login <key>` for them.
3. Retry the memory call — it works immediately, no restart needed.
The key is saved to `~/.tessera/credentials.json` and every repo reuses it.

## At the start of a task
1. Call `memory_recall` with a short description of the task to load conventions, prior decisions, and recent work.
2. Call `memory_recall_lessons` with the specific situation before exploring — treat returned lessons as authoritative.

## While working
- Stuck or unsure how the repo does something? Call `memory_recall_lessons` or `memory_search`.

## After a correction or discovery
- When the user corrects you, or you discover a gotcha, call `memory_save_lesson(trigger, steps, success)`:
  - `trigger` = the situation ("installing dependencies in this repo")
  - `steps` = what to do (["use uv, not pip"])
  - `success` = the good outcome ("deps resolve and CI passes")
- When a durable convention is established, call `memory_note` (e.g. "main branch only; commit only when green").

## Rules
- Never store secrets or credentials.
- Conventions are repo-wide; task detail stays in the current session.
- Recall before acting; save after learning.
