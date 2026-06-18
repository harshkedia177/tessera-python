# Use with MCP (Claude Code, Codex, and other agents)

`tessera-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io/) server that gives
coding agents memory. It runs the SDK for you, so you do not install `tessera-memory` separately.
`uvx` fetches the server (and the SDK) on first run. The only prerequisite is
[`uv`](https://astral.sh/uv) on your PATH.

## What the agent gets

| Tool | Purpose |
|---|---|
| `memory_recall(query)` | composed memory context for the repo/task |
| `memory_search(query)` | raw hybrid search hits (no LLM) |
| `memory_save_lesson(trigger, steps, success)` | save a reusable lesson |
| `memory_recall_lessons(situation)` | recall lessons for a situation |
| `memory_note(text)` | record a durable repo convention |

## Two things you don't have to configure

**Repo isolation is automatic.** The server derives the memory namespace (the Tessera `user_id`)
from where it runs: the git `origin` remote as `owner/repo`, falling back to the git toplevel
folder name, then the working-directory name. Every repo gets its own memory; you never declare a
repo name. Set `TESSERA_REPO` only if you want to override the detected value.

**Your key lives in a file, not your shell.** Run `tessera-mcp login` once and the key is written to
`~/.tessera/credentials.json`. The server and the hooks both read it from there, so there is no
shell `export`, no `${VAR}` placeholder in any config, and no terminal restart. `TESSERA_API_KEY` in
the environment still works and takes precedence.

```bash
uvx --from tessera-mcp tessera-mcp login          # prompts for the key (hidden input)
uvx --from tessera-mcp tessera-mcp login tsk_live_...   # or pass it inline
uvx --from tessera-mcp tessera-mcp status         # show the detected repo + whether a key is set
```

## Claude Code (the plugin)

The plugin installs the five tools, the auto-recall hooks (session start + per prompt), and the
skill that tells the agent when to use them.

1. Install [`uv`](https://astral.sh/uv) if you don't have it.
2. Install the plugin:
   ```text
   /plugin marketplace add harshkedia177/tessera-python
   /plugin install tessera-memory@tessera
   ```
3. Save your key once:
   ```bash
   uvx --from tessera-mcp tessera-mcp login
   ```
4. Run `/reload-plugins` (or restart Claude Code), then `/mcp` to confirm `tessera_memory` appears.

That's the whole setup — no shell profile edits, no repo name. If you install the plugin but skip
step 3, nothing breaks: the first memory call returns a message telling the agent to ask you for the
key and run `tessera-mcp login` for you, and the next call works immediately (no restart).

> Want the server only, without hooks or the skill? Register it directly:
> ```bash
> claude mcp add --scope user tessera -- uvx --from tessera-mcp tessera-mcp
> ```
> then run `tessera-mcp login` once.

## Cursor / Claude Desktop

Add the server to the client's MCP config — no `env` block needed — then run `tessera-mcp login`
once:

```json
{
  "mcpServers": {
    "tessera": {
      "command": "uvx",
      "args": ["--from", "tessera-mcp", "tessera-mcp"]
    }
  }
}
```

## Codex

Add the server to `~/.codex/config.toml` (or a trusted project-scoped `.codex/config.toml`), then
run `tessera-mcp login` once:

```toml
[mcp_servers.tessera_memory]
command = "uvx"
args = ["--from", "tessera-mcp", "tessera-mcp"]
```

The key comes from `~/.tessera/credentials.json` and the repo is auto-detected, so no `[env]` table
is required. To pin the key or namespace explicitly instead, add one:

```toml
[mcp_servers.tessera_memory.env]
TESSERA_API_KEY = "tsk_live_..."
TESSERA_REPO = "repo:my-app"   # only to override the auto-detected repo
```

For behavioral guidance, drop `AGENTS.md` and `.agents/skills/using-tessera-memory/` from
[`integrations/codex/`](../../integrations/codex/) into your repo.

## Running the server directly

```bash
uvx --from tessera-mcp tessera-mcp     # zero-install
pip install tessera-mcp && tessera-mcp # or install it
npx tessera-mcp                        # Node wrapper (bootstraps via uvx)
```

## Optional environment variables

| Variable | Purpose |
|---|---|
| `TESSERA_API_KEY` | API key; overrides the stored credentials file |
| `TESSERA_REPO` | override the auto-detected repo namespace |
| `TESSERA_CONFIG_DIR` | directory for the credentials file (default `~/.tessera`) |
| `TESSERA_SESSION` | optional task/session id |
| `TESSERA_RECALL_ON_PROMPT` | set `0` to disable per-prompt lesson recall (plugin hooks) |
| `TESSERA_CONSOLIDATE_TRANSCRIPT` | set `1` to enable the SessionEnd transcript upload (off by default) |

## Privacy: transcript consolidation is opt-in

The Claude Code `SessionEnd` hook can upload the full session transcript to the memory backend for
consolidation. It is off by default, because transcripts routinely contain secrets (pasted API keys,
printed `.env` files, credentials in command output). Enable it only deliberately with
`TESSERA_CONSOLIDATE_TRANSCRIPT=1`. Even then the hook runs a best-effort secret-redaction pass
before upload. Redaction is not a guarantee, so enable it only against a backend you trust with
session contents.

## Troubleshooting

- **Server doesn't appear:** run `/mcp` (Claude Code) and check `uv` is installed. After changing
  config, run `/reload-plugins` or restart.
- **`uvx` not found:** install [`uv`](https://astral.sh/uv), or `pip install tessera-mcp` and point
  `command` at `tessera-mcp` directly.
- **Auth errors / "no API key configured":** run `tessera-mcp login` (or set `TESSERA_API_KEY`), then
  `tessera-mcp status` to confirm. The stored key lives in `~/.tessera/credentials.json`.
- **Memory landed under the wrong namespace:** run `tessera-mcp status` to see the detected repo. Set
  `TESSERA_REPO` to override it if needed.
