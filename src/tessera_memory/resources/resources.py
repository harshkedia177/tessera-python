"""Resources resource — remember, upload, and recall resource ("attachment") memories."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from .._resource import AsyncAPIResource, SyncAPIResource
from ..models import (
    RecallResourcesRequest,
    RecallResourcesResponse,
    RememberResourceRequest,
    ResourceItem,
)

__all__ = ["ResourcesResource", "AsyncResourcesResource"]


# The server rejects parts not labelled with an allowed image content type (422).
_IMAGE_MIMES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _file_part(path: str | Path) -> dict[str, tuple[str, bytes, str]]:
    """Build the httpx multipart ``files`` mapping for ``POST /v1/resources/file``."""
    p = Path(path)
    content_type = (
        _IMAGE_MIMES.get(p.suffix.lower())
        or mimetypes.guess_type(p.name)[0]
        or "application/octet-stream"
    )
    return {"file": (p.name, p.read_bytes(), content_type)}


class ResourcesResource(SyncAPIResource):
    """Remember, upload, and recall resource ("attachment") memories."""

    def remember(
        self,
        *,
        blob_ref: str,
        mime: str,
        caption: str | None = None,
        image_url: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ResourceItem:
        """Store a blob handle + caption as a retrievable resource (``POST /v1/resources``).

        Supply ``caption`` to store it verbatim, or ``image_url`` to have the server
        VLM-caption a fetchable image.
        """
        req = RememberResourceRequest(
            blob_ref=blob_ref,
            mime=mime,
            caption=caption,
            image_url=image_url,
            user_id=user_id,
            session_id=session_id,
        )
        return self._client._request(
            "POST",
            "/v1/resources",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=ResourceItem,
        )

    def file(
        self,
        *,
        path: str | Path,
        blob_ref: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ResourceItem:
        """Upload an image to be VLM-captioned and embedded (``POST /v1/resources/file``)."""
        form: dict[str, str] = {"blob_ref": blob_ref}
        if user_id is not None:
            form["user_id"] = user_id
        if session_id is not None:
            form["session_id"] = session_id
        return self._client._request(
            "POST",
            "/v1/resources/file",
            json=form,
            files=_file_part(path),
            cast_to=ResourceItem,
        )

    def recall(
        self,
        *,
        query: str,
        k: int | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> RecallResourcesResponse:
        """Recall resources matching ``query`` by caption/visual content (``POST .../recall``)."""
        req = RecallResourcesRequest(
            query=query,
            k=k,
            user_id=user_id,
            session_id=session_id,
        )
        return self._client._request(
            "POST",
            "/v1/resources/recall",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=RecallResourcesResponse,
        )


class AsyncResourcesResource(AsyncAPIResource):
    """Async variant of :class:`ResourcesResource`."""

    async def remember(
        self,
        *,
        blob_ref: str,
        mime: str,
        caption: str | None = None,
        image_url: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ResourceItem:
        """Store a blob handle + caption as a retrievable resource (``POST /v1/resources``).

        Supply ``caption`` to store it verbatim, or ``image_url`` to have the server
        VLM-caption a fetchable image.
        """
        req = RememberResourceRequest(
            blob_ref=blob_ref,
            mime=mime,
            caption=caption,
            image_url=image_url,
            user_id=user_id,
            session_id=session_id,
        )
        return await self._client._request(
            "POST",
            "/v1/resources",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=ResourceItem,
        )

    async def file(
        self,
        *,
        path: str | Path,
        blob_ref: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ResourceItem:
        """Upload an image to be VLM-captioned and embedded (``POST /v1/resources/file``)."""
        form: dict[str, str] = {"blob_ref": blob_ref}
        if user_id is not None:
            form["user_id"] = user_id
        if session_id is not None:
            form["session_id"] = session_id
        return await self._client._request(
            "POST",
            "/v1/resources/file",
            json=form,
            files=_file_part(path),
            cast_to=ResourceItem,
        )

    async def recall(
        self,
        *,
        query: str,
        k: int | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> RecallResourcesResponse:
        """Recall resources matching ``query`` by caption/visual content (``POST .../recall``)."""
        req = RecallResourcesRequest(
            query=query,
            k=k,
            user_id=user_id,
            session_id=session_id,
        )
        return await self._client._request(
            "POST",
            "/v1/resources/recall",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=RecallResourcesResponse,
        )
