# Search and query

Two ways to retrieve memory. `search` gives you ranked hits to use yourself; `query` composes them
into context for a model.

## Search

Typed, ranked retrieval with no LLM in the loop:

```python
results = client.search(
    query="what coffee does Ada like?",
    top_k=5,
    user_id="ada",
)
for r in results.results:
    print(r.type, r.text, r.score)   # type is "episode" or "fact"; score is the rank
```

Restrict the kinds of item returned with `types`:

```python
client.search(query="...", types=["fact"], user_id="ada")
```

## Query

Composes retrieved memories into an answer-shaped `context` string plus structured results. May
call an LLM server-side:

```python
answer = client.query(query="what coffee does Ada like?", mode="chat", user_id="ada")
print(answer.context)        # prompt-ready string
answer.facts                 # structured TypedResult list
answer.episodes
answer.foresight             # plans / deadlines / temporary state, when present
```

`mode="chat"` returns a conversational context (and a `portrait`); `mode="reasoning"` is tuned for
analytic use.

## Filtering

Both methods accept `filters`, a list of clauses over intrinsic columns or `metadata.<key>`:

```python
client.search(
    query="coffee",
    filters=[{"field": "metadata.source", "op": "eq", "value": "onboarding"}],
    user_id="ada",
)
```

Operators: `eq`, `ne`, `in`, `gte`, `lte`, `gt`, `lt`.

## Time travel

Facts are bi-temporal (see [Concepts](../concepts.md#bi-temporal-facts)). Ask what was true, or what
was known, at a point in time:

```python
from datetime import datetime, timezone

client.search(
    query="Ada's coffee preference",
    as_of=datetime(2024, 1, 1, tzinfo=timezone.utc),        # true in the world then
    known_as_of=datetime(2024, 6, 1, tzinfo=timezone.utc),  # believed by then
    user_id="ada",
)
```

## Choosing between them

Use **`search`** when you want to rank, filter, or post-process hits yourself, or when you can't
afford an LLM call. Use **`query`** when you want a ready-to-use context block to hand to a model.
