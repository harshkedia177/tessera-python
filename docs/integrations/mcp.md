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

You need two values: `TESSERA_API_KEY` (your key) and `TESSERA_REPO` (the repo identity used as the
durable `user_id`, e.g. `repo:my-app`).

## Claude Code

Two ways to set it up. Pick one.

### Option A: the MCP server only (simplest, no shell setup)

The key is stored in Claude Code's own config and passed to the server on every launch. Nothing to
export.

1. Install [`uv`](https://astral.sh/uv) if you don't have it.
2. Register the server with your key (one command):
   ```bash
   claude mcp add --env TESSERA_API_KEY=tsk_live_... --env TESSERA_REPO=repo:my-app \
     --scope user tessera -- uvx --from tessera-mcp tessera-mcp
   ```
   `--scope user` makes it available in every project. The `--` separates Claude's flags from the
   server command.
3. Verify: `claude mcp list` (or `/mcp` inside a session) shows `tessera`.

You get the five `memory_*` tools. This path has no session hooks or skill.

### Option B: the plugin (tools + auto-recall hooks + skill)

The plugin also installs hooks that recall memory at session start and per prompt, and a skill that
tells the agent when to use the tools. The hooks run as separate scripts that read the key from your
**environment**, so this path needs the key in your shell profile (set once, persists).

1. Install [`uv`](https://astral.sh/uv).
2. Add your credentials to your shell profile once, then restart your terminal:
   ```bash
   echo 'export TESSERA_API_KEY=tsk_live_...' >> ~/.zshrc
   echo 'export TESSERA_REPO=repo:my-app'      >> ~/.zshrc
   ```
3. Install the plugin:
   ```
   /plugin marketplace add harshkedia177/tessera-python
   /plugin install tessera-memory@tessera
   ```
4. Run `/reload-plugins` (or restart Claude Code), then `/mcp` to confirm `tessera_memory` appears.

After this the tools work and the hooks recall and save automatically.

## Cursor / Claude Desktop

Add the server to the client's MCP config. The key goes in the `env` block (stored and passed on
every launch):

```json
{
  "mcpServers": {
    "tessera": {
      "command": "uvx",
      "args": ["--from", "tessera-mcp", "tessera-mcp"],
      "env": {
        "TESSERA_API_KEY": "tsk_live_...",
        "TESSERA_REPO": "repo:my-app"
      }
    }
  }
}
```

## Codex

Add the server to `~/.codex/config.toml` (or a trusted project-scoped `.codex/config.toml`). The key
goes in the `[env]` table, so Codex passes it on every launch:

```toml
[mcp_servers.tessera_memory]
command = "uvx"
args = ["--from", "tessera-mcp", "tessera-mcp"]

[mcp_servers.tessera_memory.env]
TESSERA_API_KEY = "tsk_live_..."
TESSERA_REPO = "repo:my-app"
```

To forward variables already set in your shell instead of hardcoding them, drop the `[env]` table and
use `env_vars = ["TESSERA_API_KEY", "TESSERA_REPO"]`. For behavioral guidance, drop `AGENTS.md` and
`.agents/skills/using-tessera-memory/` from [`integrations/codex/`](../../integrations/codex/) into
your repo.

## Running the server directly

```bash
uvx --from tessera-mcp tessera-mcp     # zero-install
pip install tessera-mcp && tessera-mcp # or install it
npx tessera-mcp                        # Node wrapper (bootstraps via uvx)
```

## Optional environment variables

| Variable | Purpose |
|---|---|
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
- **Auth errors:** confirm the key is in the server's config `env` (Options A / Cursor / Codex) or in
  your shell profile (Option B plugin).
