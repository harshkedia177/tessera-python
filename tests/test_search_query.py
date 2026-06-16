from __future__ import annotations

import json

import httpx
import respx

from _helpers import BASE_URL
from tessera_memory import AsyncTessera, Tessera
from tessera_memory.models import QueryResponse, SearchResponse

_SEARCH_RESPONSE = {
    "results": [
        {"id": "ep_1", "type": "episode", "text": "pizza night", "score": 0.91},
        {"id": "ft_1", "type": "fact", "text": "alice likes pizza", "score": 0.8},
    ]
}

_QUERY_RESPONSE = {
    "context": "Alice likes pizza.",
    "results": [{"id": "ft_1", "type": "fact", "text": "alice likes pizza", "score": 0.8}],
    "episodes": [],
    "facts": [{"id": "ft_1", "type": "fact", "text": "alice likes pizza", "score": 0.8}],
    "foresight": [],
    "portrait": None,
    "provenance": {"route": None, "verifier": None, "repaired": False},
}


@respx.mock
def test_search_request_shape_and_response(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/search").mock(
        return_value=httpx.Response(200, json=_SEARCH_RESPONSE)
    )
    result = client.search.search("pizza", top_k=5, user_id="u1")
    assert isinstance(result, SearchResponse)
    assert [r.id for r in result.results] == ["ep_1", "ft_1"]
    assert result.results[0].score == 0.91

    request = route.calls.last.request
    assert request.url.path == "/v1/search"
    body = json.loads(request.content)
    assert body["query"] == "pizza"
    assert body["top_k"] == 5
    assert body["user_id"] == "u1"
    assert body["rerank"] is True


@respx.mock
def test_search_callable_surface(client: Tessera) -> None:
    respx.post(f"{BASE_URL}/v1/search").mock(
        return_value=httpx.Response(200, json=_SEARCH_RESPONSE)
    )
    result = client.search("pizza", user_id="u1")
    assert isinstance(result, SearchResponse)
    assert len(result.results) == 2


@respx.mock
def test_search_with_filters_and_types(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/search").mock(
        return_value=httpx.Response(200, json=_SEARCH_RESPONSE)
    )
    client.search(
        "pizza",
        types=["fact"],
        filters=[{"field": "importance", "op": "gte", "value": 0.5}],
        rerank=False,
        user_id="u1",
    )
    body = json.loads(route.calls.last.request.content)
    assert body["types"] == ["fact"]
    assert body["rerank"] is False
    assert body["filters"] == [{"field": "importance", "op": "gte", "value": 0.5}]


@respx.mock
def test_query_request_shape_and_response(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/query").mock(
        return_value=httpx.Response(200, json=_QUERY_RESPONSE)
    )
    result = client.query.query("what does alice like?", mode="chat", user_id="u1")
    assert isinstance(result, QueryResponse)
    assert result.context == "Alice likes pizza."
    assert result.provenance.repaired is False

    body = json.loads(route.calls.last.request.content)
    assert body["query"] == "what does alice like?"
    assert body["mode"] == "chat"
    assert body["user_id"] == "u1"


@respx.mock
def test_query_callable_surface_reasoning_mode(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/query").mock(
        return_value=httpx.Response(200, json=_QUERY_RESPONSE)
    )
    result = client.query("q", mode="reasoning", user_id="u1")
    assert isinstance(result, QueryResponse)
    assert json.loads(route.calls.last.request.content)["mode"] == "reasoning"


@respx.mock
async def test_async_search(async_client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/search").mock(
        return_value=httpx.Response(200, json=_SEARCH_RESPONSE)
    )
    result = await async_client.search("pizza", user_id="u1")
    assert isinstance(result, SearchResponse)
    assert len(result.results) == 2
    await async_client.aclose()


@respx.mock
async def test_async_query(async_client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/query").mock(return_value=httpx.Response(200, json=_QUERY_RESPONSE))
    result = await async_client.query("q", user_id="u1")
    assert isinstance(result, QueryResponse)
    assert result.context == "Alice likes pizza."
    await async_client.aclose()
