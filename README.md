# tessera-memory

[![PyPI version](https://img.shields.io/pypi/v/tessera-memory.svg)](https://pypi.org/project/tessera-memory/)
[![Python versions](https://img.shields.io/pypi/pyversions/tessera-memory.svg)](https://pypi.org/project/tessera-memory/)
[![License](https://img.shields.io/pypi/l/tessera-memory.svg)](./LICENSE)
[![CI](https://github.com/harshkedia177/tessera-python/actions/workflows/ci.yml/badge.svg)](https://github.com/harshkedia177/tessera-python/actions/workflows/ci.yml)

**Long-term memory for LLM agents.** The official Python SDK for the
[Tessera](https://github.com/harshkedia177/tessera-python) memory service — write conversational turns, and recall
ranked hits or a prompt-ready context block. Sync and async clients, fully typed (Pydantic v2
models generated from the server's OpenAPI 3.1 contract).

[Getting started](./docs/getting-started.md) · [Concepts](./docs/concepts.md) · [API reference](./api.md) · [Use with MCP](./docs/integrations/mcp.md)

## Installation

```bash
pip install tessera-memory
# or
uv add tessera-memory
```

Requires Python 3.10+.

## Quickstart

```python
from tessera_memory import Tessera

# Reads TESSERA_API_KEY from the environment,
# or pass it: Tessera(api_key="tsk_live_...").
client = Tessera()

# Write a memory.
client.memories.add(content="Ada prefers dark roast coffee.", role="user", user_id="ada")

# Retrieve ranked, typed hits (no LLM).
hits = client.search(query="what coffee does Ada like?", top_k=5, user_id="ada")

# Or compose a prompt-ready context block (may call an LLM server-side).
answer = client.query(query="what coffee does Ada like?", mode="chat", user_id="ada")
print(answer.context)
```

See [Getting started](./docs/getting-started.md) for a guided walkthrough and
[Concepts](./docs/concepts.md) for how memory is structured.

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

## Configuration

| Setting | Argument            | Environment variable | Default  |
| ------- | ------------------- | -------------------- | -------- |
| API key | `Tessera(api_key=)` | `TESSERA_API_KEY`    | required |

Auth is sent as `Authorization: Bearer <key>`. Full options — timeouts, custom transport, logging,
raw responses — are in [Configuration](./docs/configuration.md).

## Pagination

`memories.list` returns a cursor page that auto-follows the cursor when you iterate it:

```python
for item in client.memories.list(user_id="ada"):   # iterates across all pages
    print(item.id, item.text)
```

Page manually with `page.has_next_page()` / `page.get_next_page()`. See
[the reference](./api.md#pagination).

## Handling errors

Every error derives from `TesseraError`. HTTP errors carry the parsed RFC 9457 problem body and the
request id.

```python
from tessera_memory import NotFoundError, RateLimitError, TesseraError

try:
    client.memories.get("ep_missing", user_id="ada")
except NotFoundError:
    ...
except RateLimitError as exc:
    print(exc.request_id)
except TesseraError:
    ...
```

| Status | Exception | | Status | Exception |
|---|---|---|---|---|
| 401 | `AuthenticationError` | | 429 | `RateLimitError` |
| 403 | `PermissionDeniedError` | | ≥ 500 | `InternalServerError` |
| 404 | `NotFoundError` | | timeout | `APITimeoutError` |
| 409 | `ConflictError` | | network | `APIConnectionError` |
| 422 | `UnprocessableEntityError` | | | |

See [Error handling](./docs/guides/error-handling.md).

## Retries

Failed requests are retried with jittered exponential backoff (default `max_retries=2`, honoring
`Retry-After`). `429`/`502`/`503` are retried for any call; an ambiguous `500`/timeout/connection
error is retried only for idempotent requests — `GET`/`DELETE` and `memories.add`, which mints a
client-side ULID `turn_id` to stay `ON CONFLICT`-safe. Other writes are not retried on ambiguous
failures, so they can't be double-applied. Override per call with
`client.with_options(max_retries=0)`. Details in
[Configuration](./docs/configuration.md#retries-and-idempotency).

## Logging

Set `TESSERA_LOG=debug` (or `info`) to log request/response lines to stderr. The `Authorization`
header, the API key, and request bodies are never logged.

## Use with MCP (Claude Code, Codex)

Expose memory to a coding agent with the `tessera-mcp` server. You don't install this SDK
separately — `uvx` fetches the server (and the SDK with it) on first run. Set `TESSERA_API_KEY`
and `TESSERA_REPO` in your shell first.

**Claude Code** — install the plugin:

```
/plugin marketplace add harshkedia177/tessera-python
/plugin install tessera-memory@tessera
```

**Codex** — add to `~/.codex/config.toml`:

```toml
[mcp_servers.tessera_memory]
command = "uvx"
args = ["--from", "tessera-mcp", "tessera-mcp"]
env_vars = ["TESSERA_API_KEY", "TESSERA_REPO"]
```

Full setup for Claude Code, Codex, Cursor, and other MCP clients — plus the privacy notes on
transcript consolidation — is in [Use with MCP](./docs/integrations/mcp.md).

## Documentation

- [Getting started](./docs/getting-started.md) — install, connect, first reads and writes.
- [Concepts](./docs/concepts.md) — turns, episodes, facts, procedures, resources.
- [Configuration](./docs/configuration.md) — clients, retries, timeouts, logging, transport.
- Guides: [memories](./docs/guides/memory.md) · [search and query](./docs/guides/search-and-query.md) · [procedures and resources](./docs/guides/procedures-and-resources.md) · [error handling](./docs/guides/error-handling.md)
- [Use with MCP](./docs/integrations/mcp.md) — Claude Code, Codex, and other agents.
- [API reference](./api.md) — the full method surface.

## Development

```bash
make sync-spec    # copy openapi.json from the server checkout
make generate     # regenerate src/tessera_memory/models.py from openapi.json
make lint         # ruff check + format --check
make typecheck    # mypy --strict
make test         # pytest (respx-mocked)
```

## License

[Apache-2.0](./LICENSE)
