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

## Configure

Two things are handled for you, so setup is one short step:

- **Repo isolation is automatic.** Memory is namespaced by the git `origin` remote (`owner/repo`),
  falling back to the folder name. You never declare a repo name.
- **The key is stored once, in a file.** Run `tessera-mcp login` and it is saved to
  `~/.tessera/credentials.json` — no shell `export`, no `${VAR}` in config, no restart.

```bash
tessera-mcp login          # prompts for your tsk_live_... key (hidden input)
tessera-mcp login tsk_live_...   # or pass it inline
tessera-mcp status         # show the detected repo + whether a key is set
```

Environment overrides (all optional, and they take precedence over the stored values):

- `TESSERA_API_KEY`: API key (overrides the credentials file)
- `TESSERA_REPO`: override the auto-detected repo namespace
- `TESSERA_CONFIG_DIR`: directory for the credentials file (default `~/.tessera`)
- `TESSERA_SESSION`: optional task/session id
- `TESSERA_RECALL_ON_PROMPT`: set `0` to disable per-prompt lesson recall (Claude Code)
- `TESSERA_CONSOLIDATE_TRANSCRIPT`: set `1` to enable the Claude Code SessionEnd
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

Register the server (no secrets in the config), then run `tessera-mcp login` once.

**Claude Code:**

```bash
claude mcp add --scope user tessera -- uvx --from tessera-mcp tessera-mcp
uvx --from tessera-mcp tessera-mcp login
```

**Cursor / Claude Desktop:**

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

**Codex:** copy the `[mcp_servers.tessera_memory]` block from `integrations/codex/config.toml` into
`~/.codex/config.toml`, then run `tessera-mcp login`.

Want session hooks (auto-recall, transcript consolidation) and the `using-tessera-memory` skill too?
Install the all-in-one plugin: `/plugin marketplace add harshkedia177/tessera-python` then
`/plugin install tessera-memory@tessera`, and run `tessera-mcp login` once. The plugin auto-detects
the repo and reads the stored key — no shell profile edits.

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
