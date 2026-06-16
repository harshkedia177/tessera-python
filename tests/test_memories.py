from __future__ import annotations

import json
from typing import Any

import httpx
import respx

from _helpers import BASE_URL
from tessera_memory import AsyncTessera, Tessera
from tessera_memory.models import (
    AsyncAddResponse,
    BatchAddResponse,
    FactItem,
    ForgetResponse,
    MemoryItem,
    PinResponse,
    SyncAddResponse,
    WipeResponse,
)


def _body(route: respx.Route) -> dict[str, Any]:
    body: dict[str, Any] = json.loads(route.calls.last.request.content)
    return body


@respx.mock
def test_add_async_default(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/memories").mock(
        return_value=httpx.Response(
            201,
            json={
                "turn_id": "t1",
                "created": True,
                "consolidation_queued": True,
                "job": {"id": "job_5", "status": "queued"},
            },
        )
    )
    result = client.memories.add(content="I love pizza", role="user", user_id="u1", session_id="s1")
    assert isinstance(result, AsyncAddResponse)
    assert result.turn_id == "t1"
    assert result.job is not None
    assert result.job.id == "job_5"

    body = _body(route)
    assert body["content"] == "I love pizza"
    assert body["role"] == "user"
    assert body["user_id"] == "u1"
    assert body["session_id"] == "s1"
    assert body["mode"] == "async"
    assert body["infer"] is True
    # A ULID turn_id was minted by the base client.
    assert isinstance(body["turn_id"], str) and len(body["turn_id"]) == 26


@respx.mock
def test_add_sync_mode_parses_sync_response(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/memories").mock(
        return_value=httpx.Response(
            200,
            json={
                "turn_id": "t2",
                "consolidation": {
                    "turns_consolidated": 1,
                    "facts_created": 2,
                    "tesserae_created": 1,
                    "foresight_created": 0,
                    "llm_calls": 3,
                },
            },
        )
    )
    result = client.memories.add(content="hi", role="user", user_id="u1", mode="sync")
    assert isinstance(result, SyncAddResponse)
    assert result.consolidation.facts_created == 2
    assert _body(route)["mode"] == "sync"


@respx.mock
def test_batch_request_and_response(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/memories:batch").mock(
        return_value=httpx.Response(
            201,
            json={
                "results": [
                    {
                        "turn_id": "t1",
                        "created": True,
                        "consolidation_queued": False,
                        "job": None,
                    },
                    {
                        "turn_id": "t2",
                        "created": True,
                        "consolidation_queued": False,
                        "job": None,
                    },
                ]
            },
        )
    )
    result = client.memories.batch(
        messages=[
            {"role": "user", "content": "one"},
            {"role": "assistant", "content": "two"},
        ],
        user_id="u1",
    )
    assert isinstance(result, BatchAddResponse)
    assert [r.turn_id for r in result.results] == ["t1", "t2"]

    assert route.calls.last.request.url.path == "/v1/memories:batch"
    body = _body(route)
    assert body["mode"] == "async"
    assert [m["content"] for m in body["messages"]] == ["one", "two"]


@respx.mock
def test_get(client: Tessera) -> None:
    route = respx.get(f"{BASE_URL}/v1/memories/ep_42").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ep_42",
                "type": "episode",
                "text": "a memory",
                "created_at": "2026-06-15T00:00:00Z",
                "metadata": {"k": "v"},
            },
        )
    )
    result = client.memories.get("ep_42")
    assert isinstance(result, MemoryItem)
    assert result.id == "ep_42"
    assert result.type.value == "episode"
    assert route.calls.last.request.method == "GET"


@respx.mock
def test_get_sends_scope_in_query_params(client: Tessera) -> None:
    route = respx.get(f"{BASE_URL}/v1/memories/ep_42").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ep_42",
                "type": "episode",
                "text": "a memory",
                "created_at": "2026-06-15T00:00:00Z",
                "metadata": {},
            },
        )
    )
    result = client.memories.get("ep_42", user_id="u1")
    assert isinstance(result, MemoryItem)
    # The server resolves ownership from query params and 422s a read carrying neither.
    assert route.calls.last.request.url.params["user_id"] == "u1"


@respx.mock
def test_delete_sends_scope_in_body(client: Tessera) -> None:
    route = respx.delete(f"{BASE_URL}/v1/memories/ep_42").mock(
        return_value=httpx.Response(
            200,
            json={
                "turns_deleted": 1,
                "tesserae_deleted": 2,
                "facts_deleted": 3,
                "foresight_deleted": 0,
            },
        )
    )
    result = client.memories.delete("ep_42", user_id="u1")
    assert isinstance(result, ForgetResponse)
    assert result.facts_deleted == 3
    assert route.calls.last.request.method == "DELETE"
    assert _body(route) == {"user_id": "u1"}


@respx.mock
def test_forget_turn(client: Tessera) -> None:
    route = respx.delete(f"{BASE_URL}/v1/memories/turns/turn_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "turns_deleted": 1,
                "tesserae_deleted": 0,
                "facts_deleted": 0,
                "foresight_deleted": 0,
            },
        )
    )
    result = client.memories.forget_turn("turn_1", user_id="u1")
    assert result.turns_deleted == 1
    assert route.calls.last.request.url.path == "/v1/memories/turns/turn_1"


@respx.mock
def test_wipe(client: Tessera) -> None:
    route = respx.delete(f"{BASE_URL}/v1/memories").mock(
        return_value=httpx.Response(200, json={"total": 17})
    )
    result = client.memories.wipe(user_id="u1")
    assert isinstance(result, WipeResponse)
    assert result.total == 17
    assert _body(route) == {"user_id": "u1"}


@respx.mock
def test_correct_patches_fact(client: Tessera) -> None:
    route = respx.patch(f"{BASE_URL}/v1/memories/ft_1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ft_2",
                "text": "alice likes tea",
                "confidence": 0.9,
                "t_valid": "2026-06-15T00:00:00Z",
                "type": "fact",
            },
        )
    )
    result = client.memories.correct("ft_1", object="tea", user_id="u1")
    assert isinstance(result, FactItem)
    assert result.id == "ft_2"
    assert route.calls.last.request.method == "PATCH"
    body = _body(route)
    assert body["object"] == "tea"
    assert body["user_id"] == "u1"


@respx.mock
def test_pin_and_unpin(client: Tessera) -> None:
    pin_route = respx.post(f"{BASE_URL}/v1/memories/ep_1/pin").mock(
        return_value=httpx.Response(200, json={"id": "ep_1", "pinned": True, "changed": True})
    )
    unpin_route = respx.delete(f"{BASE_URL}/v1/memories/ep_1/pin").mock(
        return_value=httpx.Response(200, json={"id": "ep_1", "pinned": False, "changed": True})
    )

    pinned = client.memories.pin("ep_1", user_id="u1")
    assert isinstance(pinned, PinResponse)
    assert pinned.pinned is True
    assert pin_route.calls.last.request.method == "POST"

    unpinned = client.memories.unpin("ep_1", user_id="u1")
    assert unpinned.pinned is False
    assert unpin_route.calls.last.request.method == "DELETE"


@respx.mock
async def test_async_add(async_client: AsyncTessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/memories").mock(
        return_value=httpx.Response(
            201,
            json={
                "turn_id": "t1",
                "created": True,
                "consolidation_queued": False,
                "job": None,
            },
        )
    )
    result = await async_client.memories.add(content="hi", role="user", user_id="u1")
    assert isinstance(result, AsyncAddResponse)
    assert result.turn_id == "t1"
    assert json.loads(route.calls.last.request.content)["content"] == "hi"
    await async_client.aclose()
