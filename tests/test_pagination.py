from __future__ import annotations

import httpx
import respx

from _helpers import BASE_URL
from tessera_memory import AsyncTessera, Tessera


def _item(item_id: str) -> dict[str, object]:
    return {
        "id": item_id,
        "type": "episode",
        "text": f"text for {item_id}",
        "created_at": "2026-06-15T00:00:00Z",
        "metadata": None,
    }


def _page_one() -> dict[str, object]:
    return {
        "items": [_item("ep_1"), _item("ep_2")],
        "next_cursor": "cursor-2",
        "has_more": True,
    }


def _page_two() -> dict[str, object]:
    return {
        "items": [_item("ep_3")],
        "next_cursor": None,
        "has_more": False,
    }


@respx.mock
def test_list_first_page_request_shape(client: Tessera) -> None:
    route = respx.get(f"{BASE_URL}/v1/memories").mock(
        return_value=httpx.Response(200, json=_page_one())
    )
    page = client.memories.list(user_id="u1", limit=2)
    assert [i.id for i in page.items] == ["ep_1", "ep_2"]
    assert page.has_more is True
    assert page.next_cursor == "cursor-2"

    request = route.calls.last.request
    assert request.url.params["user_id"] == "u1"
    assert request.url.params["limit"] == "2"
    # No cursor on the first request (caller passed none).
    assert "cursor" not in request.url.params


@respx.mock
def test_list_auto_follows_cursor_across_two_pages(client: Tessera) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("cursor")
        if cursor is None:
            return httpx.Response(200, json=_page_one())
        assert cursor == "cursor-2"
        return httpx.Response(200, json=_page_two())

    route = respx.get(f"{BASE_URL}/v1/memories").mock(side_effect=handler)

    page = client.memories.list(user_id="u1")
    # Iterating the page transparently follows next_cursor to the second page.
    all_ids = [item.id for item in page]
    assert all_ids == ["ep_1", "ep_2", "ep_3"]
    # Two HTTP calls: page one, then the cursor-driven page two.
    assert route.call_count == 2


@respx.mock
def test_iter_pages_yields_each_page(client: Tessera) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("cursor") is None:
            return httpx.Response(200, json=_page_one())
        return httpx.Response(200, json=_page_two())

    respx.get(f"{BASE_URL}/v1/memories").mock(side_effect=handler)

    page = client.memories.list(user_id="u1")
    pages = list(page.iter_pages())
    assert len(pages) == 2
    assert pages[0].has_next_page() is True
    assert pages[1].has_next_page() is False


@respx.mock
async def test_async_list_auto_follows_cursor(async_client: AsyncTessera) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("cursor") is None:
            return httpx.Response(200, json=_page_one())
        return httpx.Response(200, json=_page_two())

    route = respx.get(f"{BASE_URL}/v1/memories").mock(side_effect=handler)

    page = await async_client.memories.list(user_id="u1")
    collected = [item.id async for item in page]
    assert collected == ["ep_1", "ep_2", "ep_3"]
    assert route.call_count == 2
    await async_client.aclose()
