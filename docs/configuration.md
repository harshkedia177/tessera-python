# Configuration

Client construction, environment variables, and the cross-cutting behavior (retries, timeouts,
logging, transport) that applies to every request.

## Environment variables

| Variable | Used for |
|---|---|
| `TESSERA_API_KEY` | API key, sent as `Authorization: Bearer <key>`. Required. |
| `TESSERA_BASE_URL` | API base URL. Defaults to `http://localhost:8000`. |
| `TESSERA_LOG` | Set to `debug`/`info`/… to log request/response lines to stderr. |

Explicit constructor arguments take precedence over the environment.

## Constructor options

```python
from tessera_memory import Tessera

client = Tessera(
    api_key="tsk_live_...",     # else TESSERA_API_KEY
    base_url="https://...",     # else TESSERA_BASE_URL, else http://localhost:8000
    timeout=60.0,               # seconds, per request
    max_retries=2,              # up to 3 attempts total
    default_headers={"X-Team": "growth"},
)
```

`AsyncTessera` takes the same arguments (with an `httpx.AsyncClient` for `http_client`).

## Per-request overrides

`with_options` returns a copy that shares the same underlying transport, so it's cheap to call per
request. `default_headers` is merged onto the existing headers; `api_key` and `base_url` can't be
changed this way.

```python
answer = client.with_options(timeout=120.0).query(query="...", mode="chat")
fast = client.with_options(max_retries=0).health()
```

## Retries and idempotency

Retries use jittered exponential backoff and honor the `Retry-After` header. The default budget is
`max_retries=2`. What gets retried depends on *why* the request failed and whether it's safe to
replay:

- `429`, `502`, `503` — the server didn't process the request, so these are retried for **any**
  call.
- `500`, connection errors, and timeouts are ambiguous (the write may have applied), so they are
  retried **only for idempotent requests**: all `GET`/`DELETE`/`PUT`, plus `memories.add`.
- Other 4xx (`401`/`403`/`404`/`409`/`422`) are never retried.

`memories.add` is idempotent because the SDK mints a client-side ULID `turn_id` when you omit one,
making the write `ON CONFLICT`-safe on replay. Every other `POST` — `batch`, `search`, `query`,
`pin`, `procedures.record_outcome`, the maintenance calls — is **not** retried on ambiguous
failures, so it can't be silently double-applied. Supply your own `turn_id` to `add` to keep that
guarantee across process restarts.

Disable retries per call with `client.with_options(max_retries=0)`.

## Timeouts

`timeout` is seconds per request (default `60.0`). A timeout raises `APITimeoutError`. Override per
call: `client.with_options(timeout=120.0)`.

## Logging

Set `TESSERA_LOG=debug` (or `info`) to attach a stderr handler to the `tessera_memory` logger, or
configure that logger yourself. The `Authorization` header, the API key, and request bodies are
never logged.

```bash
TESSERA_LOG=debug python app.py
```

## Request IDs

Every response carries an `X-Request-Id`. Read it from a raw response or off an error to quote in
support requests:

```python
raw = client.search.with_raw_response.search(query="...")
raw.request_id

try:
    client.memories.get("ep_missing", user_id="ada")
except TesseraError as exc:
    exc.request_id  # on APIError subclasses
```

## Custom HTTP client

Pass your own `httpx` client to control proxies, TLS, or connection pooling. A client you supply is
yours to close — the SDK only closes a transport it created itself. Requests carry absolute URLs,
so your client does not need its own `base_url`.

```python
import httpx
from tessera_memory import Tessera

http = httpx.Client(proxy="http://localhost:8080", limits=httpx.Limits(max_connections=20))
client = Tessera(http_client=http)
```

## Resource management

When the SDK owns the transport, close it explicitly or use a context manager:

```python
with Tessera() as client:
    client.search(query="...", user_id="ada")

# async
async with AsyncTessera() as client:
    await client.search(query="...", user_id="ada")
```

## Raw responses

Every resource has `with_raw_response`, returning an [`APIResponse`](../api.md#apiresponse) with the
parsed model plus transport metadata (status code, headers, request id, the underlying
`httpx.Response`):

```python
raw = client.search.with_raw_response.search(query="...", user_id="ada")
raw.parsed         # the SearchResponse
raw.status_code
raw.headers        # e.g. RateLimit-*
raw.request_id
```
