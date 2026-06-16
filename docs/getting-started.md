# Getting started

This walks through your first 15 minutes with the `tessera-memory` SDK: installing, connecting,
writing memories, and reading them back.

## Install

```bash
pip install tessera-memory
# or
uv add tessera-memory
```

Requires Python 3.10+.

## Connect

The client reads `TESSERA_API_KEY` and `TESSERA_BASE_URL` from the environment, or you can pass
them directly:

```python
from tessera_memory import Tessera

client = Tessera()  # or Tessera(api_key="tsk_live_...", base_url="https://api.tessera.example")
```

Check connectivity:

```python
client.health()   # HealthStatus(status="ok")
```

## Write a memory

A memory is a single conversational turn. By default the server consolidates it asynchronously
into longer-term structures (facts, episodes) in the background:

```python
resp = client.memories.add(
    content="Ada prefers dark roast coffee.",
    role="user",
    user_id="ada",
)
resp.turn_id   # the durable id of the turn you just wrote
```

To consolidate inline and get the result back in the same call, pass `mode="sync"`:

```python
resp = client.memories.add(content="...", role="user", user_id="ada", mode="sync")
resp.consolidation.facts_created
```

See [Working with memories](guides/memory.md) for batching, correcting, pinning, and forgetting.

## Read it back

Two ways to retrieve, depending on whether you want raw hits or a composed answer.

**Search** — typed, ranked hits, no LLM:

```python
results = client.search(query="what coffee does Ada like?", top_k=5, user_id="ada")
for r in results.results:
    print(r.type, r.text, r.score)
```

**Query** — composes retrieved memories into a prompt-ready string (may call an LLM server-side):

```python
answer = client.query(query="what coffee does Ada like?", mode="chat", user_id="ada")
print(answer.context)   # drop this straight into your model prompt
```

See [Search and query](guides/search-and-query.md) for filtering, time-travel (`as_of`), and the
difference between the two.

## Async

Everything above works on `AsyncTessera` with `await`:

```python
import asyncio
from tessera_memory import AsyncTessera


async def main() -> None:
    async with AsyncTessera() as client:
        await client.memories.add(content="...", role="user", user_id="ada")
        async for item in client.memories.list(user_id="ada"):
            print(item.text)


asyncio.run(main())
```

## Next steps

- [Concepts](concepts.md) — how Tessera memory is structured.
- [Configuration](configuration.md) — retries, timeouts, logging, custom transport.
- [Use with MCP](integrations/mcp.md) — wire memory into Claude Code, Codex, and other agents.
- [API reference](../api.md) — the full method surface.
