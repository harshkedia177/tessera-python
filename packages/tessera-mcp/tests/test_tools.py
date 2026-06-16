import httpx
import respx
from tessera_mcp import tools

from conftest import BASE_URL
from tessera_memory import AsyncTessera


@respx.mock
async def test_recall_returns_context(client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/query").mock(
        return_value=httpx.Response(
            200,
            json={
                "context": "Repo uses uv, not pip.",
                "results": [],
                "episodes": [],
                "facts": [],
                "foresight": [],
                "portrait": None,
                "provenance": {"route": "easy", "verifier": False, "repaired": False},
            },
        )
    )
    out = await tools.recall(client, query="how do we install deps?", user_id="repo:demo")
    assert "uv" in out


@respx.mock
async def test_recall_empty_is_friendly(client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/query").mock(
        return_value=httpx.Response(
            200,
            json={
                "context": "",
                "results": [],
                "episodes": [],
                "facts": [],
                "foresight": [],
                "portrait": None,
                "provenance": {"route": "easy", "verifier": False, "repaired": False},
            },
        )
    )
    out = await tools.recall(client, query="x", user_id="repo:demo")
    assert out == "(no relevant memory found)"


@respx.mock
async def test_search_formats_hits(client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "ep_1",
                        "score": 0.91,
                        "text": "auth refresh in token.py",
                        "type": "episode",
                    },
                ]
            },
        )
    )
    out = await tools.search(client, query="auth", user_id="repo:demo")
    assert "token.py" in out and "0.91" in out


@respx.mock
async def test_save_lesson(client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/procedures").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "pr_1",
                "trigger": "installing deps",
                "steps": ["use uv"],
                "success": "deps resolve",
                "uses": 0,
                "last_outcome": None,
            },
        )
    )
    out = await tools.save_lesson(
        client,
        trigger="installing deps",
        steps=["use uv"],
        success="deps resolve",
        user_id="repo:demo",
    )
    assert "pr_1" in out


@respx.mock
async def test_recall_lessons(client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/procedures/recall").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "procedure": {
                            "id": "pr_1",
                            "trigger": "installing deps",
                            "steps": ["use uv"],
                            "success": "ok",
                            "uses": 3,
                            "last_outcome": True,
                        },
                        "similarity": 0.88,
                    },
                ]
            },
        )
    )
    out = await tools.recall_lessons(client, situation="adding a dependency", user_id="repo:demo")
    assert "installing deps" in out and "use uv" in out


@respx.mock
async def test_note(client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/memories").mock(
        return_value=httpx.Response(
            201,
            json={
                "turn_id": "t_1",
                "created": True,
                "consolidation_queued": False,
                "job": None,
            },
        )
    )
    out = await tools.note(client, text="main branch only; commit when green", user_id="repo:demo")
    assert "t_1" in out
