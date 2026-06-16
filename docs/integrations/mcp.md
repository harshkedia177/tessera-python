# Use with MCP (Claude Code, Codex, and other agents)

`tessera-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes
Tessera memory to coding agents. It runs the SDK for you, so you do **not** install
`tessera-memory` separately for agent use — `uvx` fetches the server (and the SDK with it) on first
run.

## What the agent gets

Five tools, plus session hooks on Claude Code that recall and save automatically:

| Tool | Purpose |
|---|---|
| `memory_recall(query)` | composed memory context for the repo/task |
| `memory_search(query)` | raw hybrid search hits (no LLM) |
| `memory_save_lesson(trigger, steps, success)` | save a reusable lesson |
| `memory_recall_lessons(situation)` | recall lessons for a situation |
| `memory_note(text)` | record a durable repo convention |

## Environment

Set these in your shell before launching the agent:

| Variable | Purpose |
|---|---|
| `TESSERA_API_KEY` | your Tessera API key (the tenant boundary) |
| `TESSERA_BASE_URL` | Tessera API base URL |
| `TESSERA_REPO` | repo identity, used as the durable `user_id` (e.g. `repo:my-app`) |
| `TESSERA_SESSION` | optional task/session id |

## Claude Code

Install the bundled plugin from the marketplace:

```
/plugin marketplace add harshkedia177/tessera-python
/plugin install tessera-memory@tessera
```

The plugin ships the MCP server, session hooks (recall at session start and per prompt, optional
transcript consolidation at session end), and the `using-tessera-memory` skill. The server
activates automatically once the plugin is enabled — run `/mcp` to confirm it appears. In a live
session, `/reload-plugins` activates it without a restart.

> **Prerequisite:** [`uv`](https://astral.sh/uv) must be on your PATH (the plugin launches the
> server with `uvx`).

## Other MCP clients (Cursor, Claude Desktop, …)

Any MCP client that takes a stdio server config can run it directly. Add this to the client's MCP
configuration:

```json
{
  "mcpServers": {
    "tessera_memory": {
      "command": "uvx",
      "args": ["--from", "tessera-mcp", "tessera-mcp"],
      "env": {
        "TESSERA_API_KEY": "${TESSERA_API_KEY}",
        "TESSERA_BASE_URL": "${TESSERA_BASE_URL}",
        "TESSERA_REPO": "${TESSERA_REPO}"
      }
    }
  }
}
```

## Codex

Add the server to `~/.codex/config.toml` (or a trusted project-scoped `.codex/config.toml`):

```toml
[mcp_servers.tessera_memory]
command = "uvx"
args = ["--from", "tessera-mcp", "tessera-mcp"]
env_vars = ["TESSERA_API_KEY", "TESSERA_BASE_URL", "TESSERA_REPO"]
```

Codex does **not** interpolate `${VAR}` inside a `[mcp_servers.*.env]` table — that table takes
literal values. To forward secrets already set in your shell, list their **names** under `env_vars`
(requires a recent Codex CLI; on older versions, set literal values under
`[mcp_servers.tessera_memory.env]` instead).

For behavioral guidance, drop `AGENTS.md` and `.agents/skills/using-tessera-memory/` from
[`integrations/codex/`](../../integrations/codex/) into your repo — the skill tells the agent when
and how to use the tools.

## Running the server directly

```bash
uvx --from tessera-mcp tessera-mcp     # zero-install
pip install tessera-mcp && tessera-mcp # or install it
npx tessera-mcp                        # Node wrapper (bootstraps via uvx)
```

## Privacy: transcript consolidation is opt-in

The Claude Code `SessionEnd` hook can upload the full session transcript to the memory backend for
consolidation. It is **off by default**, because transcripts routinely contain secrets (pasted API
keys, printed `.env` files, credentials in command output). Enable it only deliberately with
`TESSERA_CONSOLIDATE_TRANSCRIPT=1`. Even then the hook runs a best-effort secret-redaction pass
before upload — but redaction is not a guarantee, so enable it only against a backend you trust with
session contents.

## Troubleshooting

- **Server doesn't appear** — run `/mcp` (Claude Code) and check `uv` is installed. After changing
  config, `/reload-plugins` or restart.
- **`uvx` not found** — install [`uv`](https://astral.sh/uv), or use `pip install tessera-mcp` and
  point `command` at `tessera-mcp` directly.
- **Auth errors** — confirm `TESSERA_API_KEY` and `TESSERA_BASE_URL` are exported in the shell that
  launched the agent.
