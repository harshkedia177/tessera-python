# API reference

Full surface of the `tessera-memory` SDK. Every method exists on both `Tessera` (sync) and
`AsyncTessera` (async); the async form is identical with `await`. Scope parameters
(`user_id`, `session_id`) appear on nearly every method — see [Scope](#scope).

Import models from the `models` module:

```python
from tessera_memory import models
```

## Client

```python
from tessera_memory import Tessera, AsyncTessera
```

Constructor (both clients, keyword-only):

| Param | Type | Default | Notes |
|---|---|---|---|
| `api_key` | `str \| None` | `None` | Falls back to `TESSERA_API_KEY`. Required; raises `TesseraError` if absent. |
| `base_url` | `str \| None` | `None` | Optional self-hosting override. Defaults to `https://tessera.harshkedia717.workers.dev`; a `TESSERA_BASE_URL` env override is still honored. |
| `timeout` | `float` | `60.0` | Per-request timeout in seconds. |
| `max_retries` | `int` | `2` | Up to 3 attempts total. |
| `default_headers` | `dict[str, str] \| None` | `None` | Sent on every request. |
| `http_client` | `httpx.Client \| httpx.AsyncClient \| None` | `None` | Bring your own transport; the SDK won't close a client you pass. |

Top-level methods:

- `client.health() -> models.HealthStatus` — `GET /health`
- `client.ready() -> models.HealthStatus` — `GET /ready`
- `client.with_options(*, timeout=, max_retries=, default_headers=) -> Tessera | AsyncTessera` — copy sharing the same transport; `default_headers` is merged, not replaced. Cannot change `api_key`/`base_url`.
- `client.close()` / `await client.aclose()` — also usable as `with Tessera() as c:` / `async with AsyncTessera() as c:`.

Every resource exposes `.with_raw_response`, returning an [`APIResponse`](#apiresponse) instead of the parsed model:

```python
raw = client.memories.with_raw_response.get("ep_...")
```

## memories

`client.memories`

Types: `MemoryItem`, `FactItem`, `SyncAddResponse`, `AsyncAddResponse`, `BatchAddResponse`, `BatchMessage`, `PinResponse`, `ForgetResponse`, `WipeResponse`.

Methods:

- `add(*, content, role, user_id=None, session_id=None, turn_id=None, mode="async", infer=True, event_time=None, metadata=None) -> SyncAddResponse | AsyncAddResponse` — `POST /v1/memories`. `mode="sync"` consolidates inline (200, `SyncAddResponse`); `mode="async"` queues consolidation (201, `AsyncAddResponse`). Omit `turn_id` to auto-mint a ULID (makes the write retry-safe).
- `batch(*, messages, user_id=None, session_id=None, mode="async", infer=True, metadata=None) -> BatchAddResponse` — `POST /v1/memories:batch`. `messages` is a list of `BatchMessage` or dicts. Async-only consolidation.
- `list(*, user_id=None, session_id=None, limit=None, cursor=None) -> SyncCursorPage[MemoryItem]` — `GET /v1/memories`. Auto-paging, newest-first. See [Pagination](#pagination).
- `get(item_id, *, user_id=None, session_id=None) -> MemoryItem` — `GET /v1/memories/{item_id}`.
- `delete(item_id, *, user_id=None, session_id=None) -> ForgetResponse` — `DELETE /v1/memories/{item_id}`.
- `forget_turn(turn_id, *, user_id=None, session_id=None) -> ForgetResponse` — `DELETE /v1/memories/turns/{turn_id}`.
- `wipe(*, user_id=None, session_id=None) -> WipeResponse` — `DELETE /v1/memories`. Erases every record for the scope.
- `correct(item_id, *, object, confidence=None, t_valid=None, user_id=None, session_id=None) -> FactItem` — `PATCH /v1/memories/{item_id}`. **`ft_` (fact) ids only.** Revises the fact's object.
- `pin(item_id, *, user_id=None, session_id=None) -> PinResponse` — `POST /v1/memories/{item_id}/pin`. **`ep_` (episode) ids only.**
- `unpin(item_id, *, user_id=None, session_id=None) -> PinResponse` — `DELETE /v1/memories/{item_id}/pin`. **`ep_` ids only.**

## search

`client.search` — callable: `client.search(query, ...)`

Types: `SearchResponse`, `SearchResult`, `FilterClause`.

- `search(query, *, top_k=None, rerank=True, as_of=None, known_as_of=None, types=None, filters=None, user_id=None, session_id=None) -> SearchResponse` — `POST /v1/search`. Typed retrieval, no LLM. `types` filters to `["episode"]`/`["fact"]`; `filters` is a list of `FilterClause`.

## query

`client.query` — callable: `client.query(query, ...)`

Types: `QueryResponse`, `TypedResult`, `ForesightItem`, `Provenance`.

- `query(query, *, mode="chat", top_k=None, as_of=None, known_as_of=None, filters=None, user_id=None, session_id=None) -> QueryResponse` — `POST /v1/query`. Composes retrieved memories into a prompt-ready `context` string plus structured results.

## procedures

`client.procedures`

Types: `ProcedureView`, `RecallProceduresResponse`, `RecalledProcedure`.

- `remember(*, trigger, steps, success, user_id=None, session_id=None) -> ProcedureView` — `POST /v1/procedures`.
- `recall(*, task, k=None, min_similarity=None, user_id=None, session_id=None) -> RecallProceduresResponse` — `POST /v1/procedures/recall`. A read; does not change use counts.
- `record_outcome(item_id, *, success, user_id=None, session_id=None) -> ProcedureView` — `POST /v1/procedures/{item_id}/outcome`.

## resources

`client.resources`

Types: `ResourceItem`, `RecallResourcesResponse`, `RecalledResource`.

- `remember(*, blob_ref, mime, caption=None, image_url=None, user_id=None, session_id=None) -> ResourceItem` — `POST /v1/resources`. Pass `caption` to store verbatim, or `image_url` for server-side VLM captioning.
- `file(*, path, blob_ref, user_id=None, session_id=None) -> ResourceItem` — `POST /v1/resources/file` (multipart). Content type is guessed from the extension; only `.png/.jpg/.jpeg/.gif/.webp` are accepted.
- `recall(*, query, k=None, user_id=None, session_id=None) -> RecallResourcesResponse` — `POST /v1/resources/recall`.

## maintenance

`client.maintenance`

Types: `ReindexResponse`, `CompressResponse`, `EnqueuedResponse`.

- `consolidate(*, user_id=None, session_id=None) -> ConsolidationSummary | EnqueuedResponse` — `POST /v1/consolidate`. Returns the inline summary (200) or an enqueued-job handle (202) — poll it with `jobs.get`.
- `reindex(*, user_id=None, session_id=None) -> ReindexResponse` — `POST /v1/reindex`.
- `compress(*, user_id=None, session_id=None, token_budget=None) -> CompressResponse` — `POST /v1/compress`. Returns a token-budgeted `digest`.

## jobs

`client.jobs`

Types: `JobStatusResponse`.

- `get(job_id) -> JobStatusResponse` — `GET /v1/jobs/{job_id}`. No scope params. `status` is one of `queued`/`running`/`succeeded`/`failed`.

## Pagination

`memories.list` returns a `SyncCursorPage[MemoryItem]` (`AsyncCursorPage` for the async client) that auto-follows the cursor:

```python
for item in client.memories.list(user_id="ada"):   # iterates across all pages
    ...

# Manual page control:
page = client.memories.list(user_id="ada", limit=50)
page.items          # list[MemoryItem] for this page
page.has_more       # bool
page.next_cursor    # str | None
if page.has_next_page():
    page = page.get_next_page()
```

Async: `async for item in client.memories.list(user_id="ada"): ...`

## APIResponse

Returned by `<resource>.with_raw_response.<method>(...)`:

```python
@dataclass(frozen=True)
class APIResponse:
    parsed: Any                  # the model the method normally returns
    status_code: int
    headers: httpx.Headers
    request_id: str | None       # X-Request-Id
    http_response: httpx.Response
```

## Exceptions

```
TesseraError
├── APIConnectionError          # no response: DNS/TCP/TLS/dropped socket — attr: request
│   └── APITimeoutError         # request timed out
└── APIError                    # server returned a response — attrs: status_code, problem, request_id, response
    └── APIStatusError          # non-2xx (carries parsed ProblemDetail)
        ├── AuthenticationError       # 401
        ├── PermissionDeniedError     # 403
        ├── NotFoundError             # 404
        ├── ConflictError             # 409
        ├── UnprocessableEntityError  # 422
        ├── RateLimitError            # 429
        └── InternalServerError       # >= 500
```

`APIError`/`APIStatusError` expose `.status_code`, `.problem` (an RFC 9457 `ProblemDetail` with
`status`/`title`/`detail`/`type`/`instance`), `.request_id`, and `.response`.

## Scope

`user_id` and `session_id` are partition labels, not authentication (the API key is the tenant
boundary). The server generally requires at least one of the pair; an empty pair returns `422`
(`UnprocessableEntityError`). On reads (`get`, `list`) scope travels as query parameters; on writes
and deletes it travels in the JSON body.
