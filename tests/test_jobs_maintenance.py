from __future__ import annotations

import json

import httpx
import respx

from _helpers import BASE_URL
from tessera_memory import AsyncTessera, Tessera
from tessera_memory.models import (
    CompressResponse,
    EnqueuedResponse,
    JobStatusResponse,
    ReindexResponse,
    TesseraApiV1MaintenanceConsolidationSummary,
)


@respx.mock
def test_jobs_get(client: Tessera) -> None:
    route = respx.get(f"{BASE_URL}/v1/jobs/job_7").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "job_7",
                "kind": "consolidate",
                "status": "running",
                "created_at": "2026-06-15T00:00:00Z",
                "updated_at": "2026-06-15T00:00:05Z",
                "error": None,
            },
        )
    )
    result = client.jobs.get("job_7")
    assert isinstance(result, JobStatusResponse)
    assert result.status.value == "running"
    assert route.calls.last.request.url.path == "/v1/jobs/job_7"


@respx.mock
def test_consolidate_sync_summary(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/consolidate").mock(
        return_value=httpx.Response(
            200,
            json={
                "turns_consolidated": 3,
                "facts_created": 5,
                "tesserae_created": 2,
                "foresight_created": 1,
                "llm_calls": 9,
            },
        )
    )
    result = client.maintenance.consolidate(user_id="u1")
    assert isinstance(result, TesseraApiV1MaintenanceConsolidationSummary)
    assert result.facts_created == 5
    assert json.loads(route.calls.last.request.content) == {"user_id": "u1"}


@respx.mock
def test_consolidate_async_enqueued(client: Tessera) -> None:
    respx.post(f"{BASE_URL}/v1/consolidate").mock(
        return_value=httpx.Response(
            202,
            json={"job": {"id": "job_9", "status": "queued"}},
        )
    )
    result = client.maintenance.consolidate(user_id="u1")
    assert isinstance(result, EnqueuedResponse)
    assert result.job.id == "job_9"


@respx.mock
def test_reindex(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/reindex").mock(
        return_value=httpx.Response(200, json={"panels_refreshed": 4, "turns_backfilled": 2})
    )
    result = client.maintenance.reindex(user_id="u1")
    assert isinstance(result, ReindexResponse)
    assert result.panels_refreshed == 4
    assert route.calls.last.request.url.path == "/v1/reindex"


@respx.mock
def test_compress(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/compress").mock(
        return_value=httpx.Response(200, json={"digest": "summary block"})
    )
    result = client.maintenance.compress(user_id="u1", token_budget=500)
    assert isinstance(result, CompressResponse)
    assert result.digest == "summary block"
    body = json.loads(route.calls.last.request.content)
    assert body["user_id"] == "u1"
    assert body["token_budget"] == 500


@respx.mock
async def test_async_jobs_get(async_client: AsyncTessera) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_7").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "job_7",
                "kind": "consolidate",
                "status": "succeeded",
                "created_at": "2026-06-15T00:00:00Z",
                "updated_at": "2026-06-15T00:00:05Z",
                "error": None,
            },
        )
    )
    result = await async_client.jobs.get("job_7")
    assert result.status.value == "succeeded"
    await async_client.aclose()
