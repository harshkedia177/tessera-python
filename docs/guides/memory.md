# Working with memories

The `memories` resource covers the full lifecycle of a memory: write, browse, correct, pin, and
forget. See [Concepts](../concepts.md) for what episodes and facts are.

## Add a turn

```python
resp = client.memories.add(
    content="Ada prefers dark roast coffee.",
    role="user",                       # "system" | "user" | "assistant"
    user_id="ada",
    metadata={"source": "onboarding"}, # optional, stored verbatim
)
resp.turn_id
```

`mode="async"` (default) queues consolidation and returns an `AsyncAddResponse`; `mode="sync"`
consolidates inline and returns a `SyncAddResponse` with a `consolidation` summary. Pass
`infer=False` to store the turn without deriving facts/episodes from it.

The SDK mints a ULID `turn_id` when you omit one, which makes the write safe to retry. Supply your
own to keep it idempotent across process restarts:

```python
client.memories.add(content="...", role="user", user_id="ada", turn_id="my-stable-id")
```

## Add many at once

```python
resp = client.memories.batch(
    messages=[
        {"content": "Hi, I'm Ada.", "role": "user"},
        {"content": "Nice to meet you, Ada.", "role": "assistant"},
    ],
    user_id="ada",
)
resp.results   # one AsyncAddResponse per message, in order
```

## Browse

`list` returns an auto-paging cursor over `MemoryItem`, newest first:

```python
for item in client.memories.list(user_id="ada"):
    print(item.id, item.type, item.text)
```

See [Pagination](../../api.md#pagination) for manual page control.

## Fetch one

```python
item = client.memories.get("ep_2f...", user_id="ada")
```

## Correct a fact

Facts (`ft_` ids) can be revised. Only the object changes — the subject and relation are fixed:

```python
fact = client.memories.correct(
    "ft_9c...",
    object="oat milk",
    confidence=0.9,
    user_id="ada",
)
```

## Pin an episode

Pinning protects an episode (`ep_` ids) from being forgotten during consolidation:

```python
client.memories.pin("ep_2f...", user_id="ada")
client.memories.unpin("ep_2f...", user_id="ada")
```

## Forget

```python
client.memories.delete("ep_2f...", user_id="ada")        # one item + its dependents
client.memories.forget_turn("turn_abc", user_id="ada")   # everything derived from a turn
client.memories.wipe(user_id="ada")                      # erase the whole partition
```

Each returns counts of what was removed. `wipe` is the right-to-be-forgotten path — it deletes
every record for the scope.
