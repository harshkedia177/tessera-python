from __future__ import annotations

import httpx
import pytest
import respx

from _helpers import API_KEY, BASE_URL
from tessera_memory import AsyncTessera, Tessera
from tessera_memory._base_client import DEFAULT_BASE_URL
from tessera_memory._exceptions import TesseraError
from tessera_memory.models import HealthStatus


def test_api_key_and_base_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESSERA_API_KEY", "tsk_from_env")
    monkeypatch.setenv("TESSERA_BASE_URL", "https://env.tessera.test/")
    client = Tessera()
    assert client.api_key == "tsk_from_env"
    # Trailing slash is stripped so path joins stay clean.
    assert client.base_url == "https://env.tessera.test"


def test_explicit_args_override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESSERA_API_KEY", "tsk_from_env")
    monkeypatch.setenv("TESSERA_BASE_URL", "https://env.tessera.test")
    client = Tessera(api_key="tsk_explicit", base_url="https://explicit.tessera.test")
    assert client.api_key == "tsk_explicit"
    assert client.base_url == "https://explicit.tessera.test"


def test_default_base_url_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TESSERA_BASE_URL", raising=False)
    client = Tessera(api_key="tsk_x")
    assert client.base_url == DEFAULT_BASE_URL


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    with pytest.raises(TesseraError, match="No API key provided"):
        Tessera()


@respx.mock
def test_auth_header_and_user_agent_sent(client: Tessera) -> None:
    route = respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.health()
    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"].startswith("tessera-memory-python/")


@respx.mock
def test_default_headers_merged(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Tessera(
        api_key=API_KEY,
        base_url=BASE_URL,
        default_headers={"X-Tenant": "acme"},
    )
    route = respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.health()
    assert route.calls.last.request.headers["X-Tenant"] == "acme"
    client.close()


@respx.mock
def test_health_probe(client: Tessera) -> None:
    respx.get(f"{BASE_URL}/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
    result = client.health()
    assert isinstance(result, HealthStatus)
    assert result.status.value == "ok"


@respx.mock
def test_ready_probe(client: Tessera) -> None:
    route = respx.get(f"{BASE_URL}/ready").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    result = client.ready()
    assert result.status.value == "ok"
    assert route.calls.last.request.url.path == "/ready"


@respx.mock
async def test_async_health_probe(async_client: AsyncTessera) -> None:
    respx.get(f"{BASE_URL}/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
    result = await async_client.health()
    assert result.status.value == "ok"
    await async_client.aclose()


def test_sync_context_manager_closes() -> None:
    with Tessera(api_key=API_KEY, base_url=BASE_URL) as client:
        assert isinstance(client, Tessera)
    assert client._http.is_closed


async def test_async_context_manager_closes() -> None:
    async with AsyncTessera(api_key=API_KEY, base_url=BASE_URL) as client:
        assert isinstance(client, AsyncTessera)
    assert client._http.is_closed
