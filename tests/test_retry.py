from __future__ import annotations

import json

import httpx
import pytest
import respx

from _helpers import BASE_URL, problem_json
from tessera_memory import (
    APIConnectionError,
    APITimeoutError,
    AsyncTessera,
    RateLimitError,
    Tessera,
)

_OK_JOB = {
    "id": "job_1",
    "kind": "consolidate",
    "status": "succeeded",
    "created_at": "2026-06-15T00:00:00Z",
    "updated_at": "2026-06-15T00:00:01Z",
}


@respx.mock
def test_429_then_200_succeeds_and_backs_off(client: Tessera, recorded_sleeps: list[float]) -> None:
    route = respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        side_effect=[
            httpx.Response(429, json=problem_json(429, title="Too Many Requests")),
            httpx.Response(200, json=_OK_JOB),
        ]
    )
    result = client.jobs.get("job_1")
    assert result.status.value == "succeeded"
    assert route.call_count == 2
    # Exactly one backoff slept between the two attempts.
    assert len(recorded_sleeps) == 1
    assert recorded_sleeps[0] > 0


@respx.mock
def test_429_honours_retry_after_header(client: Tessera, recorded_sleeps: list[float]) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        side_effect=[
            httpx.Response(
                429,
                json=problem_json(429, title="Too Many Requests"),
                headers={"Retry-After": "3"},
            ),
            httpx.Response(200, json=_OK_JOB),
        ]
    )
    client.jobs.get("job_1")
    # Retry-After is honoured verbatim (no jitter applied).
    assert recorded_sleeps == [3.0]


@respx.mock
def test_500_retried_then_exhausts(client: Tessera, recorded_sleeps: list[float]) -> None:
    route = respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        return_value=httpx.Response(500, json=problem_json(500, title="Internal Server Error"))
    )
    client.max_retries = 2
    with pytest.raises(Exception):  # noqa: B017 - exhaustion raises the mapped 500 error
        client.jobs.get("job_1")
    # Initial attempt + 2 retries = 3 calls; 2 backoffs.
    assert route.call_count == 3
    assert len(recorded_sleeps) == 2


@respx.mock
def test_429_exhausts_to_rate_limit_error(client: Tessera, recorded_sleeps: list[float]) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        return_value=httpx.Response(429, json=problem_json(429, title="Too Many Requests"))
    )
    client.max_retries = 1
    with pytest.raises(RateLimitError):
        client.jobs.get("job_1")


@respx.mock
def test_connection_error_maps_to_api_connection_error(
    client: Tessera, recorded_sleeps: list[float]
) -> None:
    route = respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    with pytest.raises(APIConnectionError):
        client.jobs.get("job_1")
    # Connection errors are retried up to max_retries (default 2) -> 3 attempts.
    assert route.call_count == 3


@respx.mock
def test_connection_error_then_success(client: Tessera, recorded_sleeps: list[float]) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        side_effect=[httpx.ConnectError("boom"), httpx.Response(200, json=_OK_JOB)]
    )
    result = client.jobs.get("job_1")
    assert result.status.value == "succeeded"
    assert len(recorded_sleeps) == 1


@respx.mock
def test_timeout_maps_to_api_timeout_error(client: Tessera, recorded_sleeps: list[float]) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(side_effect=httpx.ReadTimeout("timed out"))
    with pytest.raises(APITimeoutError):
        client.jobs.get("job_1")


@respx.mock
def test_idempotent_re_add_mints_and_reuses_turn_id(
    client: Tessera, recorded_sleeps: list[float]
) -> None:
    seen_turn_ids: list[str] = []

    def capture(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen_turn_ids.append(body["turn_id"])
        if len(seen_turn_ids) == 1:
            return httpx.Response(429, json=problem_json(429, title="Too Many Requests"))
        return httpx.Response(
            201,
            json={
                "turn_id": body["turn_id"],
                "created": True,
                "consolidation_queued": True,
                "job": None,
            },
        )

    respx.post(f"{BASE_URL}/v1/memories").mock(side_effect=capture)
    result = client.memories.add(content="hi", role="user", user_id="u1")

    assert len(seen_turn_ids) == 2
    # The minted turn_id is non-empty and identical across the retry (ON CONFLICT-safe).
    assert seen_turn_ids[0]
    assert seen_turn_ids[0] == seen_turn_ids[1]
    assert result.turn_id == seen_turn_ids[0]


@respx.mock
def test_supplied_turn_id_is_not_overwritten(client: Tessera, recorded_sleeps: list[float]) -> None:
    route = respx.post(f"{BASE_URL}/v1/memories").mock(
        return_value=httpx.Response(
            201,
            json={
                "turn_id": "my-turn",
                "created": True,
                "consolidation_queued": False,
                "job": None,
            },
        )
    )
    client.memories.add(content="hi", role="user", user_id="u1", turn_id="my-turn")
    body = json.loads(route.calls.last.request.content)
    assert body["turn_id"] == "my-turn"


def _add_201() -> httpx.Response:
    return httpx.Response(
        201,
        json={"turn_id": "t", "created": True, "consolidation_queued": True, "job": None},
    )


@respx.mock
def test_non_idempotent_post_500_is_not_retried(
    client: Tessera, recorded_sleeps: list[float]
) -> None:
    route = respx.post(f"{BASE_URL}/v1/memories:batch").mock(
        return_value=httpx.Response(500, json=problem_json(500, title="Internal Server Error"))
    )
    with pytest.raises(Exception):  # noqa: B017
        client.memories.batch(messages=[{"content": "hi", "role": "user"}], user_id="u1")
    assert route.call_count == 1  # no retry on an ambiguous failure for a non-idempotent POST
    assert recorded_sleeps == []


@respx.mock
def test_non_idempotent_post_503_is_retried(client: Tessera, recorded_sleeps: list[float]) -> None:
    """503 means 'not processed', so even a non-idempotent write is safe to replay."""
    route = respx.post(f"{BASE_URL}/v1/memories:batch").mock(
        side_effect=[
            httpx.Response(503, json=problem_json(503, title="Unavailable")),
            httpx.Response(201, json={"results": []}),
        ]
    )
    client.memories.batch(messages=[{"content": "hi", "role": "user"}], user_id="u1")
    assert route.call_count == 2


@respx.mock
def test_non_idempotent_post_timeout_is_not_retried(
    client: Tessera, recorded_sleeps: list[float]
) -> None:
    route = respx.post(f"{BASE_URL}/v1/memories:batch").mock(side_effect=httpx.ReadTimeout("t"))
    with pytest.raises(APITimeoutError):
        client.memories.batch(messages=[{"content": "hi", "role": "user"}], user_id="u1")
    assert route.call_count == 1  # ambiguous: a timed-out write may have applied


@respx.mock
def test_idempotent_add_500_is_retried(client: Tessera, recorded_sleeps: list[float]) -> None:
    """POST /v1/memories carries a minted turn_id, so a 500 IS safe to replay."""
    route = respx.post(f"{BASE_URL}/v1/memories").mock(
        side_effect=[
            httpx.Response(500, json=problem_json(500, title="Internal Server Error")),
            _add_201(),
        ]
    )
    client.memories.add(content="hi", role="user", user_id="u1")
    assert route.call_count == 2


@respx.mock
async def test_async_429_then_200_succeeds(
    async_client: AsyncTessera, recorded_sleeps: list[float]
) -> None:
    route = respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        side_effect=[
            httpx.Response(429, json=problem_json(429, title="Too Many Requests")),
            httpx.Response(200, json=_OK_JOB),
        ]
    )
    result = await async_client.jobs.get("job_1")
    assert result.status.value == "succeeded"
    assert route.call_count == 2
    assert len(recorded_sleeps) == 1
    await async_client.aclose()


@respx.mock
async def test_async_connection_error(
    async_client: AsyncTessera, recorded_sleeps: list[float]
) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(APIConnectionError):
        await async_client.jobs.get("job_1")
    await async_client.aclose()
