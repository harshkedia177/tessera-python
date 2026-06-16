from __future__ import annotations

import logging

import httpx
import pytest
import respx

from _helpers import API_KEY, BASE_URL
from tessera_memory import APIResponse, AsyncTessera, Tessera

_OK_JOB = {
    "id": "job_1",
    "kind": "consolidate",
    "status": "succeeded",
    "created_at": "2026-06-15T00:00:00Z",
    "updated_at": "2026-06-15T00:00:01Z",
}


@respx.mock
def test_injected_http_client_is_used_and_not_closed() -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(return_value=httpx.Response(200, json=_OK_JOB))
    transport = httpx.Client()
    client = Tessera(api_key=API_KEY, base_url=BASE_URL, http_client=transport)

    assert client._http is transport
    assert client.jobs.get("job_1").status.value == "succeeded"

    client.close()
    assert not transport.is_closed
    transport.close()


@respx.mock
def test_owned_http_client_is_closed() -> None:
    client = Tessera(api_key=API_KEY, base_url=BASE_URL)
    http = client._http
    client.close()
    assert http.is_closed


def test_with_options_overrides_only_named_fields() -> None:
    client = Tessera(api_key=API_KEY, base_url=BASE_URL, max_retries=2, timeout=60.0)
    scoped = client.with_options(timeout=5.0)

    assert scoped.timeout == 5.0
    assert scoped.max_retries == 2
    assert client.timeout == 60.0
    # The copy shares the transport rather than opening a new pool.
    assert scoped._http is client._http
    assert scoped._owns_http is False
    client.close()


def test_with_options_max_retries_zero_is_respected() -> None:
    """``0`` is a real value, not 'unset' — the sentinel must distinguish them."""
    client = Tessera(api_key=API_KEY, base_url=BASE_URL, max_retries=2)
    assert client.with_options(max_retries=0).max_retries == 0
    client.close()


@respx.mock
def test_with_options_max_retries_zero_disables_retry() -> None:
    route = respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        return_value=httpx.Response(503, json={"status": 503, "title": "Unavailable"})
    )
    client = Tessera(api_key=API_KEY, base_url=BASE_URL)
    with pytest.raises(Exception):  # noqa: B017
        client.with_options(max_retries=0).jobs.get("job_1")
    assert route.call_count == 1
    client.close()


@respx.mock
def test_with_options_merges_default_headers(client: Tessera) -> None:
    route = respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.with_options(default_headers={"X-Trace": "abc"}).health()
    assert route.calls.last.request.headers["X-Trace"] == "abc"


@respx.mock
def test_with_raw_response_returns_envelope(client: Tessera) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        return_value=httpx.Response(
            200, json=_OK_JOB, headers={"X-Request-Id": "req_123", "RateLimit-Remaining": "9"}
        )
    )
    raw = client.jobs.with_raw_response.get("job_1")
    assert isinstance(raw, APIResponse)
    assert raw.parsed.status.value == "succeeded"
    assert raw.status_code == 200
    assert raw.request_id == "req_123"
    assert raw.headers["RateLimit-Remaining"] == "9"
    assert isinstance(raw.http_response, httpx.Response)


@respx.mock
def test_plain_call_after_raw_call_is_not_sticky(client: Tessera) -> None:
    """The raw-mode ContextVar must reset so a later plain call returns the bare model."""
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(return_value=httpx.Response(200, json=_OK_JOB))
    client.jobs.with_raw_response.get("job_1")
    plain = client.jobs.get("job_1")
    assert not isinstance(plain, APIResponse)
    assert plain.status.value == "succeeded"


@respx.mock
async def test_async_with_raw_response(async_client: AsyncTessera) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        return_value=httpx.Response(200, json=_OK_JOB, headers={"X-Request-Id": "req_async"})
    )
    raw = await async_client.jobs.with_raw_response.get("job_1")
    assert isinstance(raw, APIResponse)
    assert raw.request_id == "req_async"
    plain = await async_client.jobs.get("job_1")
    assert not isinstance(plain, APIResponse)
    await async_client.aclose()


@respx.mock
def test_user_agent_carries_python_and_os(client: Tessera) -> None:
    route = respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.health()
    ua = route.calls.last.request.headers["User-Agent"]
    assert ua.startswith("tessera-memory-python/")
    assert "Python/" in ua


@respx.mock
def test_authorization_header_is_never_logged(
    client: Tessera, caplog: pytest.LogCaptureFixture
) -> None:
    respx.get(f"{BASE_URL}/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
    with caplog.at_level(logging.DEBUG, logger="tessera_memory"):
        client.health()
    blob = " ".join(r.getMessage() for r in caplog.records)
    assert "Bearer" not in blob
    assert API_KEY not in blob
    assert "/health" in blob  # the request line itself is still logged
