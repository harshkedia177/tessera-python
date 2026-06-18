<div align="center">

# tessera-memory

**Long-term memory for LLM agents.**

Your agent forgets everything between sessions. Tessera remembers. Write conversational
turns, then recall ranked hits or a prompt-ready context block. Sync and async, fully typed.

[![PyPI version](https://img.shields.io/pypi/v/tessera-memory.svg?v=0.1.1)](https://pypi.org/project/tessera-memory/)
[![Python versions](https://img.shields.io/pypi/pyversions/tessera-memory.svg?v=0.1.1)](https://pypi.org/project/tessera-memory/)
[![License](https://img.shields.io/pypi/l/tessera-memory.svg?v=0.1.1)](https://github.com/harshkedia177/tessera-python/blob/main/LICENSE)
[![CI](https://github.com/harshkedia177/tessera-python/actions/workflows/ci.yml/badge.svg)](https://github.com/harshkedia177/tessera-python/actions/workflows/ci.yml)

[Getting started](https://github.com/harshkedia177/tessera-python/blob/main/docs/getting-started.md) · [Concepts](https://github.com/harshkedia177/tessera-python/blob/main/docs/concepts.md) · [API reference](https://github.com/harshkedia177/tessera-python/blob/main/api.md) · [Use with MCP](https://github.com/harshkedia177/tessera-python/blob/main/docs/integrations/mcp.md)

</div>

## What you get

| | |
|---|---|
| 🧠 **Memory** | Extracts facts and episodes from conversation turns. Handles corrections, pinning, and forgetting. |
| 🔍 **Search** | Ranked, typed retrieval over your memory. No LLM in the loop, so it stays cheap and deterministic. |
| 💬 **Query** | Composes retrieved memory into a prompt-ready context block for your model. |
| 📚 **Procedures** | Store reusable lessons (trigger, steps, outcome) and recall them by task. |
| ⚡ **Sync + async** | The same typed API on `Tessera` and `AsyncTessera`. |
| 🔌 **MCP built in** | Give Claude Code, Codex, and Cursor memory with one server. |

## Install

```bash
pip install tessera-memory   # or: uv add tessera-memory
```

Requires Python 3.10+.

## Quickstart

```python
from tessera_memory import Tessera

client = Tessera()  # reads TESSERA_API_KEY, or Tessera(api_key="tsk_live_...")

# Write what happened.
client.memories.add(content="Ada prefers dark roast coffee.", role="user", user_id="ada")

# Get ranked hits (no LLM)...
hits = client.search(query="what coffee does Ada like?", user_id="ada")

# ...or a prompt-ready context block (may call an LLM server-side).
answer = client.query(query="what coffee does Ada like?", mode="chat", user_id="ada")
print(answer.context)
```

That is the whole loop: `add` to remember, `search` to retrieve, `query` to get context for a model.

## Async

Every method exists on `AsyncTessera` with `await`:

```python
import asyncio
from tessera_memory import AsyncTessera


async def main() -> None:
    async with AsyncTessera() as client:
        await client.memories.add(content="Ada prefers dark roast coffee.", role="user", user_id="ada")
        async for item in client.memories.list(user_id="ada"):
            print(item.text)


asyncio.run(main())
```

## Use with MCP (Claude Code, Codex, Cursor)

Give your coding agent memory with the `tessera-mcp` server. `uvx` fetches it (and the SDK) on
first run, so there's nothing to install. Two things are handled for you:

- **Repo isolation is automatic.** Memory is namespaced per git repo (from the `origin`
  remote, falling back to the folder name). You never declare a repo name.
- **Your key is stored once, in a file.** Run `tessera-mcp login` and the key is saved to
  `~/.tessera/credentials.json` — no shell `export`, no `${VAR}` in config, no restart.

**Claude Code (one-step plugin).** Install the plugin, then save your key once:

```text
/plugin marketplace add harshkedia177/tessera-python
/plugin install tessera-memory@tessera
```

```bash
uvx --from tessera-mcp tessera-mcp login   # paste your tsk_live_... key when prompted
```

That's it — you get the five `memory_*` tools, auto-recall hooks, and the skill. (If you
skip the login step, the first memory call simply tells the agent to ask you for the key
and run it for you.)

**Cursor / Claude Desktop.** Add the server (no `env` block needed), then run the same
`tessera-mcp login` once:

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

**Codex.** Add to `~/.codex/config.toml`, then run `tessera-mcp login` once:

```toml
[mcp_servers.tessera_memory]
command = "uvx"
args = ["--from", "tessera-mcp", "tessera-mcp"]
```

> Prefer the environment? `TESSERA_API_KEY` (key) and `TESSERA_REPO` (to override the
> auto-detected namespace) still work everywhere and take precedence over the stored values.

Full details — the all-in-one Claude Code plugin, hooks, and the privacy notes on transcript
consolidation — are in [Use with MCP](https://github.com/harshkedia177/tessera-python/blob/main/docs/integrations/mcp.md).

## Configuration

The client reads `TESSERA_API_KEY` from the environment, or you pass it directly. Auth goes out as
a bearer token. For timeouts, retries, logging, raw responses, and a custom HTTP client, see
[Configuration](https://github.com/harshkedia177/tessera-python/blob/main/docs/configuration.md).

## Documentation

- [Getting started](https://github.com/harshkedia177/tessera-python/blob/main/docs/getting-started.md): install, connect, first reads and writes.
- [Concepts](https://github.com/harshkedia177/tessera-python/blob/main/docs/concepts.md): turns, episodes, facts, procedures, resources.
- [Configuration](https://github.com/harshkedia177/tessera-python/blob/main/docs/configuration.md): clients, retries, timeouts, logging, transport.
- Guides: [memories](https://github.com/harshkedia177/tessera-python/blob/main/docs/guides/memory.md) · [search and query](https://github.com/harshkedia177/tessera-python/blob/main/docs/guides/search-and-query.md) · [procedures and resources](https://github.com/harshkedia177/tessera-python/blob/main/docs/guides/procedures-and-resources.md) · [error handling](https://github.com/harshkedia177/tessera-python/blob/main/docs/guides/error-handling.md)
- [API reference](https://github.com/harshkedia177/tessera-python/blob/main/api.md): the full method surface.

## Development

```bash
make sync-spec    # copy openapi.json from the server checkout
make generate     # regenerate src/tessera_memory/models.py from openapi.json
make lint         # ruff check + format --check
make typecheck    # mypy --strict
make test         # pytest (respx-mocked)
```

## License

Apache 2.0. See [LICENSE](https://github.com/harshkedia177/tessera-python/blob/main/LICENSE).
