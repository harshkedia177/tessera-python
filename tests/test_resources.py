from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

from _helpers import BASE_URL
from tessera_memory import AsyncTessera, Tessera
from tessera_memory.models import (
    RecallResourcesResponse,
    ResourceItem,
)

_RESOURCE = {
    "id": "ep_res_1",
    "caption": "a photo of a cat",
    "blob_ref": "blob://abc",
    "mime": "image/png",
}


@respx.mock
def test_remember(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/resources").mock(
        return_value=httpx.Response(201, json=_RESOURCE)
    )
    result = client.resources.remember(
        blob_ref="blob://abc",
        mime="image/png",
        caption="a photo of a cat",
        user_id="u1",
    )
    assert isinstance(result, ResourceItem)
    assert result.id == "ep_res_1"

    body = json.loads(route.calls.last.request.content)
    assert body["blob_ref"] == "blob://abc"
    assert body["mime"] == "image/png"
    assert body["caption"] == "a photo of a cat"
    # image_url omitted -> excluded from the body.
    assert "image_url" not in body


@respx.mock
def test_recall(client: Tessera) -> None:
    route = respx.post(f"{BASE_URL}/v1/resources/recall").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"resource": _RESOURCE, "similarity": 0.77}]},
        )
    )
    result = client.resources.recall(query="cat", k=5, user_id="u1")
    assert isinstance(result, RecallResourcesResponse)
    assert result.results[0].similarity == 0.77
    assert result.results[0].resource.blob_ref == "blob://abc"

    body = json.loads(route.calls.last.request.content)
    assert body["query"] == "cat"
    assert body["k"] == 5


@respx.mock
def test_file_upload_multipart(client: Tessera, tmp_path: Path) -> None:
    img = tmp_path / "cat.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\nFAKEDATA")

    route = respx.post(f"{BASE_URL}/v1/resources/file").mock(
        return_value=httpx.Response(201, json=_RESOURCE)
    )
    result = client.resources.file(path=img, blob_ref="blob://abc", user_id="u1")
    assert isinstance(result, ResourceItem)

    request = route.calls.last.request
    assert request.url.path == "/v1/resources/file"
    content_type = request.headers["Content-Type"]
    assert content_type.startswith("multipart/form-data")
    # The raw multipart body carries the form fields and the file bytes.
    raw = request.content
    assert b'name="file"' in raw
    assert b'filename="cat.png"' in raw
    # The part must declare an allowlisted image MIME (server rejects octet-stream).
    assert b"Content-Type: image/png" in raw
    assert b"application/octet-stream" not in raw
    assert b"FAKEDATA" in raw
    assert b'name="blob_ref"' in raw
    assert b"blob://abc" in raw
    assert b'name="user_id"' in raw


@respx.mock
async def test_async_remember(async_client: AsyncTessera) -> None:
    respx.post(f"{BASE_URL}/v1/resources").mock(return_value=httpx.Response(201, json=_RESOURCE))
    result = await async_client.resources.remember(
        blob_ref="blob://abc", mime="image/png", caption="cat", user_id="u1"
    )
    assert isinstance(result, ResourceItem)
    assert result.caption == "a photo of a cat"
    await async_client.aclose()
