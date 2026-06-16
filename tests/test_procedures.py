from __future__ import annotations

import json

import httpx
import respx

from _helpers import BASE_URL
from tessera_memory import AsyncTessera, Tessera
from tessera_memory.models import (
    ProcedureView,
    RecallProceduresResponse,
)

_PROCEDURE = {
    "id": "ep_proc_1",
    "trigger": "deploy the app",
    "steps": ["build", "push", "rollout"],
    "success": "health check passes",
    "uses": 0,
    "last_outcome": None,
}


@respx.mock
def test_remember(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/procedures").mock(
        return_value=httpx.Response(201, json=_PROCEDURE)
    )
    result = client.procedures.remember(
        trigger="deploy the app",
        steps=["build", "push", "rollout"],
        success="health check passes",
        user_id="u1",
    )
    assert isinstance(result, ProcedureView)
    assert result.id == "ep_proc_1"
    assert result.uses == 0

    body = json.loads(route.calls.last.request.content)
    assert body["trigger"] == "deploy the app"
    assert body["steps"] == ["build", "push", "rollout"]
    assert body["success"] == "health check passes"
    assert body["user_id"] == "u1"


@respx.mock
def test_recall(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/procedures/recall").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"procedure": _PROCEDURE, "similarity": 0.88}]},
        )
    )
    result = client.procedures.recall(task="ship a release", k=3, min_similarity=0.5, user_id="u1")
    assert isinstance(result, RecallProceduresResponse)
    assert result.results[0].similarity == 0.88
    assert result.results[0].procedure.id == "ep_proc_1"

    body = json.loads(route.calls.last.request.content)
    assert body["task"] == "ship a release"
    assert body["k"] == 3
    assert body["min_similarity"] == 0.5


@respx.mock
def test_record_outcome(client: Tessera) -> None:
    applied = {**_PROCEDURE, "uses": 1, "last_outcome": True}
    route = respx.post(f"{BASE_URL}/v1/procedures/ep_proc_1/outcome").mock(
        return_value=httpx.Response(200, json=applied)
    )
    result = client.procedures.record_outcome("ep_proc_1", success=True, user_id="u1")
    assert isinstance(result, ProcedureView)
    assert result.uses == 1
    assert result.last_outcome is True
    assert route.calls.last.request.url.path == "/v1/procedures/ep_proc_1/outcome"
    assert json.loads(route.calls.last.request.content)["success"] is True


@respx.mock
async def test_async_recall(async_client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/procedures/recall").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"procedure": _PROCEDURE, "similarity": 0.7}]},
        )
    )
    result = await async_client.procedures.recall(task="ship", user_id="u1")
    assert result.results[0].similarity == 0.7
    await async_client.aclose()
