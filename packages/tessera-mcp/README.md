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

- `TESSERA_API_KEY`: your Tessera API key (the tenant/isolation boundary)
- `TESSERA_REPO`: repo identity, used as the durable `user_id` (e.g. `repo:my-app`)
- `TESSERA_SESSION`: optional task/session id
- `TESSERA_RECALL_ON_PROMPT`: set `0` to disable per-prompt lesson recall (Claude Code)
- `TESSERA_CONSOLIDATE_TRANSCRIPT`: set `1` to enable the Claude Code SessionEnd
  transcript upload (default off). See the warning below.

Put `TESSERA_API_KEY` and `TESSERA_REPO` in the MCP client config (the `env` block of the server
entry, or `claude mcp add --env`), not your shell. The client stores them and passes them to the
server on every launch, so there is no `export` to re-run each session. See Editor setup below.

## Tools

| Tool | Purpose |
|---|---|
| `memory_recall(query)` | composed memory context for the repo/task |
| `memory_search(query)` | raw hybrid search hits (no LLM) |
| `memory_save_lesson(trigger, steps, success)` | save a reusable lesson |
| `memory_recall_lessons(situation)` | recall lessons for a situation |
| `memory_note(text)` | record a durable repo convention |

## Editor setup

The key lives in the config and is passed on every launch (no shell `export`).

**Claude Code:**

```bash
claude mcp add --env TESSERA_API_KEY=tsk_live_... --env TESSERA_REPO=repo:my-app \
  --scope user tessera -- uvx --from tessera-mcp tessera-mcp
```

**Cursor / Claude Desktop:**

```json
{
  "mcpServers": {
    "tessera": {
      "command": "uvx",
      "args": ["--from", "tessera-mcp", "tessera-mcp"],
      "env": { "TESSERA_API_KEY": "tsk_live_...", "TESSERA_REPO": "repo:my-app" }
    }
  }
}
```

**Codex:** copy the `[mcp_servers.tessera_memory]` block from `integrations/codex/config.toml` into
`~/.codex/config.toml` (key goes in its `[env]` table).

Want session hooks (auto-recall, transcript consolidation) and the `using-tessera-memory` skill too?
Install the all-in-one plugin: `/plugin marketplace add harshkedia177/tessera-python` then
`/plugin install tessera-memory@tessera`. The plugin reads `TESSERA_API_KEY` / `TESSERA_REPO` from
the environment, so set those in your shell profile if you use it.

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

Redaction is best-effort, not a guarantee. Enable transcript consolidation only
against a memory backend you trust with session contents.
