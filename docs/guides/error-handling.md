# Error handling

Every error the SDK raises derives from `TesseraError`, so one `except` clause catches them all.

```python
from tessera_memory import Tessera, TesseraError, RateLimitError, NotFoundError

client = Tessera()

try:
    client.memories.get("ep_missing", user_id="ada")
except NotFoundError:
    ...                      # 404
except RateLimitError as exc:
    exc.request_id           # quote this in support requests
except TesseraError:
    ...                      # anything else
```

## Hierarchy

| Status | Exception |
|---|---|
| 401 | `AuthenticationError` |
| 403 | `PermissionDeniedError` |
| 404 | `NotFoundError` |
| 409 | `ConflictError` |
| 422 | `UnprocessableEntityError` |
| 429 | `RateLimitError` |
| ≥ 500 | `InternalServerError` |
| other non-2xx | `APIStatusError` |
| network (DNS/TCP/TLS/dropped) | `APIConnectionError` |
| timeout | `APITimeoutError` |

`APIConnectionError` and `APITimeoutError` derive from `TesseraError` directly (there was no HTTP
response). Everything with a response derives from `APIError` → `APIStatusError`.

## Error details

HTTP errors carry the parsed RFC 9457 problem body:

```python
try:
    client.memories.add(content="", role="user")   # missing scope -> 422
except APIStatusError as exc:
    exc.status_code     # 422
    exc.problem.title   # short summary
    exc.problem.detail  # human-readable explanation
    exc.request_id      # X-Request-Id for correlation
```

## A note on retries

`429`/`502`/`503` and ambiguous failures on idempotent calls are retried automatically before an
exception surfaces (see [Configuration](../configuration.md#retries-and-idempotency)). By the time
you catch a `RateLimitError`, the SDK has already exhausted the retry budget.
