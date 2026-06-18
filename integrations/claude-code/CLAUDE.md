# Tessera memory is available

This project is wired to Tessera long-term memory via MCP tools
(`memory_recall`, `memory_search`, `memory_save_lesson`, `memory_recall_lessons`,
`memory_note`) and the `using-tessera-memory` skill.

- Recall relevant memory at the start of every task.
- Save a lesson after any correction or non-obvious discovery.
- See the `using-tessera-memory` skill for exactly when and how.

Setup is one step: the memory is namespaced per git repo automatically (no repo name to
declare), and the only thing to provide is the API key. If a memory tool replies that no
key is configured, ask the user for their Tessera API key and run
`uvx --from tessera-mcp tessera-mcp login <key>` — it persists and every repo picks it up.

## Transcript consolidation is opt-in (privacy)

The `SessionEnd` hook can upload the full session transcript (all user + assistant
turns) to the memory backend for consolidation. This is **off by default** because
transcripts can contain secrets. Enable it only deliberately by setting
`TESSERA_CONSOLIDATE_TRANSCRIPT=1`. Even when enabled the hook runs a best-effort
secret-redaction pass before upload, but redaction is not a guarantee — do not rely
on it alone, and never paste real credentials into the session.
