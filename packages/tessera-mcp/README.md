# tessera-mcp

MCP server exposing Tessera memory to AI coding agents (Claude Code, Codex).

## Install / run

- With the SDK:  `pip install tessera-memory[mcp]`
- MCP only (Python):  `pip install tessera-mcp`  then `tessera-mcp`
- MCP only (Node):  `npx tessera-mcp`
- Zero-install:  `uvx --from tessera-mcp tessera-mcp`

> **npm wrapper / uv bootstrap.** `npx tessera-mcp` launches the Python server via
> `uvx`. If `uv` is not on your PATH the wrapper will **not** silently install it.
> It prints instructions and exits. To let the wrapper download and run the
> official uv installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`, or the
> PowerShell equivalent on Windows), re-run with `TESSERA_AUTO_INSTALL_UV=1`.
> Alternatively install uv yourself from <https://astral.sh/uv> or use the Python
> install path above.

## Configure (env)

- `TESSERA_API_KEY` — your Tessera API key (the tenant/isolation boundary)
- `TESSERA_REPO` — repo identity, used as the durable `user_id` (e.g. `repo:my-app`)
- `TESSERA_SESSION` — optional task/session id
- `TESSERA_RECALL_ON_PROMPT` — set `0` to disable per-prompt lesson recall (Claude Code)
- `TESSERA_CONSOLIDATE_TRANSCRIPT` — set `1` to enable the Claude Code SessionEnd
  transcript upload (default off). See the warning below.

## Tools

| Tool | Purpose |
|---|---|
| `memory_recall(query)` | composed memory context for the repo/task |
| `memory_search(query)` | raw hybrid search hits (no LLM) |
| `memory_save_lesson(trigger, steps, success)` | save a reusable lesson |
| `memory_recall_lessons(situation)` | recall lessons for a situation |
| `memory_note(text)` | record a durable repo convention |

## Editor setup

- Claude Code: install the plugin — `/plugin marketplace add harshkedia177/tessera-python` then
  `/plugin install tessera-memory@tessera`. Bundles the MCP server, session hooks, and the
  `using-tessera-memory` skill (see `integrations/claude-code/`).
- Codex: copy the `[mcp_servers.tessera_memory]` block into `~/.codex/config.toml` and drop
  `AGENTS.md` + `.agents/skills/using-tessera-memory/` into your repo (see `integrations/codex/`).

## Privacy: the Claude Code SessionEnd hook ships your transcript

The Claude Code `SessionEnd` hook can upload the **entire session transcript**
(every user + assistant turn) to the memory backend, keyed by repo, where it is
later recalled and re-injected into future sessions. Coding transcripts routinely
contain secrets (pasted API keys, printed `.env` files, credentials in command
output). Because this upload is automatic, it bypasses the agent's "never store
secrets" instruction.

For that reason it is **opt-in and off by default**:

- It runs only when `TESSERA_CONSOLIDATE_TRANSCRIPT=1`.
- When enabled, a redaction pass strips common secret shapes (`KEY=`/`TOKEN=`/
  `SECRET=`/`PASSWORD=` assignments, `sk-`/`tsk_`/`ghp_`/`xox` tokens, AWS access
  keys, `Authorization:` headers, PEM private-key blocks) before upload.

Redaction is best-effort, not a guarantee — enable transcript consolidation only
against a memory backend you trust with session contents.
