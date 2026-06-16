from __future__ import annotations

import httpx
import pytest
import respx

from _helpers import BASE_URL, problem_json
from tessera_memory import (
    AsyncTessera,
    AuthenticationError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    Tessera,
    UnprocessableEntityError,
)
from tessera_memory._exceptions import APIStatusError

_CASES = [
    (401, AuthenticationError, "Unauthorized"),
    (403, PermissionDeniedError, "Forbidden"),
    (404, NotFoundError, "Not Found"),
    (409, ConflictError, "Conflict"),
    (422, UnprocessableEntityError, "Unprocessable Entity"),
    (429, RateLimitError, "Too Many Requests"),
    (500, InternalServerError, "Internal Server Error"),
]


@pytest.mark.parametrize(("status", "exc_cls", "title"), _CASES)
@respx.mock
def test_status_maps_to_exception(
    client: Tessera,
    status: int,
    exc_cls: type[APIStatusError],
    title: str,
) -> None:
    detail = f"a sanitized {status} explanation"
    respx.get(f"{BASE_URL}/v1/jobs/job_1").mock(
        return_value=httpx.Response(
            status,
            json=problem_json(status, title=title, detail=detail),
            headers={"X-Request-Id": "req-abc"},
        )
    )
    # max_retries=0 so a retryable status (429/500) surfaces immediately, not after retries.
    client.max_retries = 0
    with pytest.raises(exc_cls) as excinfo:
        client.jobs.get("job_1")

    err = excinfo.value
    assert err.status_code == status
    assert err.request_id == "req-abc"
    assert err.problem is not None
    assert err.problem.title == title
    assert err.problem.detail == detail
    # The human-readable message prefers the problem detail.
    assert str(err) == detail


@respx.mock
def test_message_falls_back_to_title_then_generic(client: Tessera) -> None:
    # No detail -> message uses the title.
    respx.get(f"{BASE_URL}/v1/jobs/job_2").mock(
        return_value=httpx.Response(404, json=problem_json(404, title="Not Found"))
    )
    with pytest.raises(NotFoundError) as excinfo:
        client.jobs.get("job_2")
    assert str(excinfo.value) == "Not Found"


@respx.mock
def test_non_problem_body_still_maps(client: Tessera) -> None:
    # A non-JSON / non-problem body must not crash the parser; problem is just None.
    respx.get(f"{BASE_URL}/v1/jobs/job_3").mock(
        return_value=httpx.Response(404, text="plain text error")
    )
    with pytest.raises(NotFoundError) as excinfo:
        client.jobs.get("job_3")
    assert excinfo.value.problem is None
    assert "404" in str(excinfo.value)


@respx.mock
def test_unmapped_4xx_falls_back_to_status_error(client: Tessera) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_4").mock(
        return_value=httpx.Response(418, json=problem_json(418, title="I'm a teapot"))
    )
    with pytest.raises(APIStatusError) as excinfo:
        client.jobs.get("job_4")
    # 418 has no dedicated subclass; it is the generic APIStatusError, not a 5xx.
    assert type(excinfo.value) is APIStatusError
    assert excinfo.value.status_code == 418


@respx.mock
async def test_async_status_maps_to_exception(async_client: AsyncTessera) -> None:
    respx.get(f"{BASE_URL}/v1/jobs/job_9").mock(
        return_value=httpx.Response(403, json=problem_json(403, title="Forbidden"))
    )
    with pytest.raises(PermissionDeniedError):
        await async_client.jobs.get("job_9")
    await async_client.aclose()
