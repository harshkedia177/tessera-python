# Tessera memory (read this first)

This repo has long-term memory via the `tessera_memory` MCP server. Tools:
`memory_recall`, `memory_search`, `memory_save_lesson`, `memory_recall_lessons`, `memory_note`.
The `using-tessera-memory` skill (`.agents/skills/`) covers exactly when and how to use them.

## Workflow
- At the start of every task, call `memory_recall` (task description) and
  `memory_recall_lessons` (the specific situation) before exploring.
- After the user corrects you or you discover a gotcha, call
  `memory_save_lesson(trigger, steps, success)`.
- Record durable conventions with `memory_note`.
- Never store secrets. Recall before acting; save after learning.

Required config: `TESSERA_API_KEY` and `TESSERA_REPO`, set in the
`[mcp_servers.tessera_memory.env]` table of `~/.codex/config.toml`.
