"""Memories resource — add, browse, fetch, correct, pin, and forget memory items."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from .._pagination import AsyncCursorPage, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from ..models import (
    AddMemoryRequest,
    AsyncAddResponse,
    BatchAddRequest,
    BatchAddResponse,
    BatchMessage,
    FactCorrectionRequest,
    FactItem,
    FieldScopedBody,
    ForgetResponse,
    MemoryItem,
    PageMemoryItem,
    PinResponse,
    SyncAddResponse,
    WipeRequest,
    WipeResponse,
)

__all__ = ["MemoriesResource", "AsyncMemoriesResource"]

_LIST_PATH = "/v1/memories"


def _scope_params(*, user_id: str | None, session_id: str | None) -> dict[str, Any]:
    """Build the ``{user_id?, session_id?}`` query string shared by scope-enforcing GETs."""
    params: dict[str, Any] = {}
    if user_id is not None:
        params["user_id"] = user_id
    if session_id is not None:
        params["session_id"] = session_id
    return params


def _list_params(
    *,
    user_id: str | None,
    session_id: str | None,
    limit: int | None,
    cursor: str | None,
) -> dict[str, Any]:
    """Build the query string for ``GET /v1/memories``, dropping unset optionals."""
    params = _scope_params(user_id=user_id, session_id=session_id)
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    return params


class MemoriesResource(SyncAPIResource):
    """Add, browse, fetch, correct, pin, and forget memory items."""

    def add(
        self,
        *,
        content: str,
        role: Literal["system", "user", "assistant"],
        user_id: str | None = None,
        session_id: str | None = None,
        turn_id: str | None = None,
        mode: Literal["sync", "async"] = "async",
        infer: bool = True,
        event_time: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SyncAddResponse | AsyncAddResponse:
        """Append one turn (``POST /v1/memories``).

        ``mode="sync"`` consolidates inline (200); ``mode="async"`` queues it (201). Omit
        ``turn_id`` to let the server mint a ULID (supplying one makes the write retry-safe).
        """
        req = AddMemoryRequest(
            content=content,
            role=role,  # type: ignore[arg-type]
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            mode=mode,  # type: ignore[arg-type]
            infer=infer,
            event_time=event_time,
            metadata=metadata,
        )
        cast_to: type[SyncAddResponse | AsyncAddResponse] = (
            SyncAddResponse if mode == "sync" else AsyncAddResponse
        )
        return self._client._request(
            "POST",
            "/v1/memories",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=cast_to,
        )

    def batch(
        self,
        *,
        messages: list[BatchMessage] | list[dict[str, Any]],
        user_id: str | None = None,
        session_id: str | None = None,
        mode: Literal["async"] = "async",
        infer: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> BatchAddResponse:
        """Append many turns sequentially under one scope (``POST /v1/memories:batch``)."""
        req = BatchAddRequest(
            messages=[m if isinstance(m, BatchMessage) else BatchMessage(**m) for m in messages],
            user_id=user_id,
            session_id=session_id,
            mode=mode,  # batch is async-only
            infer=infer,
            metadata=metadata,
        )
        return self._client._request(
            "POST",
            "/v1/memories:batch",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=BatchAddResponse,
        )

    def list(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> SyncCursorPage[MemoryItem]:
        """Browse memories newest-first (``GET /v1/memories``); auto-follows cursor pages."""

        def fetch(next_cursor: str | None) -> SyncCursorPage[MemoryItem]:
            page: PageMemoryItem = self._client._request(
                "GET",
                _LIST_PATH,
                params=_list_params(
                    user_id=user_id,
                    session_id=session_id,
                    limit=limit,
                    cursor=next_cursor,
                ),
                cast_to=PageMemoryItem,
            )
            return SyncCursorPage(
                items=page.items,
                next_cursor=page.next_cursor,
                has_more=page.has_more,
                fetch_next=lambda c: fetch(c),
            )

        return fetch(cursor)

    def get(
        self,
        item_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> MemoryItem:
        """Fetch one memory by id (``GET /v1/memories/{item_id}``); scope travels as query."""
        return self._client._request(
            "GET",
            f"/v1/memories/{item_id}",
            params=_scope_params(user_id=user_id, session_id=session_id),
            cast_to=MemoryItem,
        )

    def delete(
        self,
        item_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ForgetResponse:
        """Forget one memory and its dependents (``DELETE /v1/memories/{item_id}``)."""
        body = FieldScopedBody(user_id=user_id, session_id=session_id)
        return self._client._request(
            "DELETE",
            f"/v1/memories/{item_id}",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=ForgetResponse,
        )

    def forget_turn(
        self,
        turn_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ForgetResponse:
        """Forget every memory derived from one turn (``DELETE /v1/memories/turns/{turn_id}``)."""
        body = FieldScopedBody(user_id=user_id, session_id=session_id)
        return self._client._request(
            "DELETE",
            f"/v1/memories/turns/{turn_id}",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=ForgetResponse,
        )

    def wipe(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> WipeResponse:
        """Erase every record for a user, right-to-be-forgotten (``DELETE /v1/memories``)."""
        body = WipeRequest(user_id=user_id, session_id=session_id)
        return self._client._request(
            "DELETE",
            "/v1/memories",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=WipeResponse,
        )

    def correct(
        self,
        item_id: str,
        *,
        object: str,
        confidence: float | None = None,
        t_valid: datetime | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> FactItem:
        """Bi-temporally correct a fact edge's object, ``ft_`` ids only.

        ``PATCH /v1/memories/{item_id}``. Only the object is revised; subject/relation stay fixed.
        """
        req = FactCorrectionRequest(
            object=object,
            confidence=confidence,
            t_valid=t_valid,
            user_id=user_id,
            session_id=session_id,
        )
        return self._client._request(
            "PATCH",
            f"/v1/memories/{item_id}",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=FactItem,
        )

    def pin(
        self,
        item_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> PinResponse:
        """Pin an episode against forgetting, ``ep_`` ids only (``POST .../{item_id}/pin``)."""
        body = FieldScopedBody(user_id=user_id, session_id=session_id)
        return self._client._request(
            "POST",
            f"/v1/memories/{item_id}/pin",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=PinResponse,
        )

    def unpin(
        self,
        item_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> PinResponse:
        """Remove an episode's pin, ``ep_`` ids only (``DELETE .../{item_id}/pin``)."""
        body = FieldScopedBody(user_id=user_id, session_id=session_id)
        return self._client._request(
            "DELETE",
            f"/v1/memories/{item_id}/pin",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=PinResponse,
        )


class AsyncMemoriesResource(AsyncAPIResource):
    """Async variant of :class:`MemoriesResource`."""

    async def add(
        self,
        *,
        content: str,
        role: Literal["system", "user", "assistant"],
        user_id: str | None = None,
        session_id: str | None = None,
        turn_id: str | None = None,
        mode: Literal["sync", "async"] = "async",
        infer: bool = True,
        event_time: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SyncAddResponse | AsyncAddResponse:
        """Append one turn (``POST /v1/memories``).

        ``mode="sync"`` consolidates inline (200); ``mode="async"`` queues it (201). Omit
        ``turn_id`` to let the server mint a ULID (supplying one makes the write retry-safe).
        """
        req = AddMemoryRequest(
            content=content,
            role=role,  # type: ignore[arg-type]
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            mode=mode,  # type: ignore[arg-type]
            infer=infer,
            event_time=event_time,
            metadata=metadata,
        )
        cast_to: type[SyncAddResponse | AsyncAddResponse] = (
            SyncAddResponse if mode == "sync" else AsyncAddResponse
        )
        return await self._client._request(
            "POST",
            "/v1/memories",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=cast_to,
        )

    async def batch(
        self,
        *,
        messages: list[BatchMessage] | list[dict[str, Any]],
        user_id: str | None = None,
        session_id: str | None = None,
        mode: Literal["async"] = "async",
        infer: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> BatchAddResponse:
        """Append many turns sequentially under one scope (``POST /v1/memories:batch``)."""
        req = BatchAddRequest(
            messages=[m if isinstance(m, BatchMessage) else BatchMessage(**m) for m in messages],
            user_id=user_id,
            session_id=session_id,
            mode=mode,  # batch is async-only
            infer=infer,
            metadata=metadata,
        )
        return await self._client._request(
            "POST",
            "/v1/memories:batch",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=BatchAddResponse,
        )

    async def list(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncCursorPage[MemoryItem]:
        """Browse memories newest-first (``GET /v1/memories``); auto-follows cursor pages."""

        async def fetch(next_cursor: str | None) -> AsyncCursorPage[MemoryItem]:
            page: PageMemoryItem = await self._client._request(
                "GET",
                _LIST_PATH,
                params=_list_params(
                    user_id=user_id,
                    session_id=session_id,
                    limit=limit,
                    cursor=next_cursor,
                ),
                cast_to=PageMemoryItem,
            )
            return AsyncCursorPage(
                items=page.items,
                next_cursor=page.next_cursor,
                has_more=page.has_more,
                fetch_next=lambda c: fetch(c),
            )

        return await fetch(cursor)

    async def get(
        self,
        item_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> MemoryItem:
        """Fetch one memory by id (``GET /v1/memories/{item_id}``); scope travels as query."""
        return await self._client._request(
            "GET",
            f"/v1/memories/{item_id}",
            params=_scope_params(user_id=user_id, session_id=session_id),
            cast_to=MemoryItem,
        )

    async def delete(
        self,
        item_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ForgetResponse:
        """Forget one memory and its dependents (``DELETE /v1/memories/{item_id}``)."""
        body = FieldScopedBody(user_id=user_id, session_id=session_id)
        return await self._client._request(
            "DELETE",
            f"/v1/memories/{item_id}",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=ForgetResponse,
        )

    async def forget_turn(
        self,
        turn_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ForgetResponse:
        """Forget every memory derived from one turn (``DELETE /v1/memories/turns/{turn_id}``)."""
        body = FieldScopedBody(user_id=user_id, session_id=session_id)
        return await self._client._request(
            "DELETE",
            f"/v1/memories/turns/{turn_id}",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=ForgetResponse,
        )

    async def wipe(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> WipeResponse:
        """Erase every record for a user, right-to-be-forgotten (``DELETE /v1/memories``)."""
        body = WipeRequest(user_id=user_id, session_id=session_id)
        return await self._client._request(
            "DELETE",
            "/v1/memories",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=WipeResponse,
        )

    async def correct(
        self,
        item_id: str,
        *,
        object: str,
        confidence: float | None = None,
        t_valid: datetime | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> FactItem:
        """Bi-temporally correct a fact edge's object, ``ft_`` ids only.

        ``PATCH /v1/memories/{item_id}``. Only the object is revised; subject/relation stay fixed.
        """
        req = FactCorrectionRequest(
            object=object,
            confidence=confidence,
            t_valid=t_valid,
            user_id=user_id,
            session_id=session_id,
        )
        return await self._client._request(
            "PATCH",
            f"/v1/memories/{item_id}",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=FactItem,
        )

    async def pin(
        self,
        item_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> PinResponse:
        """Pin an episode against forgetting, ``ep_`` ids only (``POST .../{item_id}/pin``)."""
        body = FieldScopedBody(user_id=user_id, session_id=session_id)
        return await self._client._request(
            "POST",
            f"/v1/memories/{item_id}/pin",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=PinResponse,
        )

    async def unpin(
        self,
        item_id: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> PinResponse:
        """Remove an episode's pin, ``ep_`` ids only (``DELETE .../{item_id}/pin``)."""
        body = FieldScopedBody(user_id=user_id, session_id=session_id)
        return await self._client._request(
            "DELETE",
            f"/v1/memories/{item_id}/pin",
            json=body.model_dump(mode="json", exclude_none=True),
            cast_to=PinResponse,
        )
