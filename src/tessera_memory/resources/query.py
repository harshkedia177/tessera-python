"""Query resource — compose retrieved memories into an answer-shaped context."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from .._resource import AsyncAPIResource, SyncAPIResource
from ..models import FilterClause, QueryRequest, QueryResponse

__all__ = ["QueryResource", "AsyncQueryResource"]


class QueryResource(SyncAPIResource):
    """Compose retrieved memories into an answer-shaped context (callable as client.query)."""

    def query(
        self,
        query: str,
        *,
        mode: Literal["chat", "reasoning"] = "chat",
        top_k: int | None = None,
        as_of: datetime | None = None,
        known_as_of: datetime | None = None,
        filters: list[FilterClause] | list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> QueryResponse:
        """Compose a memory context for ``query`` via ``POST /v1/query``."""
        req = QueryRequest.model_validate(
            {
                "query": query,
                "mode": mode,
                "top_k": top_k,
                "as_of": as_of,
                "known_as_of": known_as_of,
                "filters": filters,
                "user_id": user_id,
                "session_id": session_id,
            }
        )
        return self._client._request(
            "POST",
            "/v1/query",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=QueryResponse,
        )

    def __call__(
        self,
        query: str,
        *,
        mode: Literal["chat", "reasoning"] = "chat",
        top_k: int | None = None,
        as_of: datetime | None = None,
        known_as_of: datetime | None = None,
        filters: list[FilterClause] | list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> QueryResponse:
        return self.query(
            query,
            mode=mode,
            top_k=top_k,
            as_of=as_of,
            known_as_of=known_as_of,
            filters=filters,
            user_id=user_id,
            session_id=session_id,
        )


class AsyncQueryResource(AsyncAPIResource):
    """Async variant of QueryResource (callable via ``await client.query(...)``)."""

    async def query(
        self,
        query: str,
        *,
        mode: Literal["chat", "reasoning"] = "chat",
        top_k: int | None = None,
        as_of: datetime | None = None,
        known_as_of: datetime | None = None,
        filters: list[FilterClause] | list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> QueryResponse:
        """Compose a memory context for ``query`` via ``POST /v1/query``."""
        req = QueryRequest.model_validate(
            {
                "query": query,
                "mode": mode,
                "top_k": top_k,
                "as_of": as_of,
                "known_as_of": known_as_of,
                "filters": filters,
                "user_id": user_id,
                "session_id": session_id,
            }
        )
        return await self._client._request(
            "POST",
            "/v1/query",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=QueryResponse,
        )

    async def __call__(
        self,
        query: str,
        *,
        mode: Literal["chat", "reasoning"] = "chat",
        top_k: int | None = None,
        as_of: datetime | None = None,
        known_as_of: datetime | None = None,
        filters: list[FilterClause] | list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> QueryResponse:
        return await self.query(
            query,
            mode=mode,
            top_k=top_k,
            as_of=as_of,
            known_as_of=known_as_of,
            filters=filters,
            user_id=user_id,
            session_id=session_id,
        )
