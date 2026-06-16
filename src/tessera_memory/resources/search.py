"""Search resource — typed, non-LLM retrieval over stored memories."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .._resource import AsyncAPIResource, SyncAPIResource
from ..models import FilterClause, SearchRequest, SearchResponse

__all__ = ["SearchResource", "AsyncSearchResource"]


class SearchResource(SyncAPIResource):
    """Run a typed, non-LLM retrieval over stored memories (callable as client.search)."""

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        rerank: bool = True,
        as_of: datetime | None = None,
        known_as_of: datetime | None = None,
        types: list[str] | None = None,
        filters: list[FilterClause] | list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> SearchResponse:
        """Retrieve typed hits for ``query`` via ``POST /v1/search``."""
        req = SearchRequest.model_validate(
            {
                "query": query,
                "top_k": top_k,
                "rerank": rerank,
                "as_of": as_of,
                "known_as_of": known_as_of,
                "types": types,
                "filters": filters,
                "user_id": user_id,
                "session_id": session_id,
            }
        )
        return self._client._request(
            "POST",
            "/v1/search",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=SearchResponse,
        )

    def __call__(
        self,
        query: str,
        *,
        top_k: int | None = None,
        rerank: bool = True,
        as_of: datetime | None = None,
        known_as_of: datetime | None = None,
        types: list[str] | None = None,
        filters: list[FilterClause] | list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> SearchResponse:
        return self.search(
            query,
            top_k=top_k,
            rerank=rerank,
            as_of=as_of,
            known_as_of=known_as_of,
            types=types,
            filters=filters,
            user_id=user_id,
            session_id=session_id,
        )


class AsyncSearchResource(AsyncAPIResource):
    """Async variant of SearchResource (callable via ``await client.search(...)``)."""

    async def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        rerank: bool = True,
        as_of: datetime | None = None,
        known_as_of: datetime | None = None,
        types: list[str] | None = None,
        filters: list[FilterClause] | list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> SearchResponse:
        """Retrieve typed hits for ``query`` via ``POST /v1/search``."""
        req = SearchRequest.model_validate(
            {
                "query": query,
                "top_k": top_k,
                "rerank": rerank,
                "as_of": as_of,
                "known_as_of": known_as_of,
                "types": types,
                "filters": filters,
                "user_id": user_id,
                "session_id": session_id,
            }
        )
        return await self._client._request(
            "POST",
            "/v1/search",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=SearchResponse,
        )

    async def __call__(
        self,
        query: str,
        *,
        top_k: int | None = None,
        rerank: bool = True,
        as_of: datetime | None = None,
        known_as_of: datetime | None = None,
        types: list[str] | None = None,
        filters: list[FilterClause] | list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> SearchResponse:
        return await self.search(
            query,
            top_k=top_k,
            rerank=rerank,
            as_of=as_of,
            known_as_of=known_as_of,
            types=types,
            filters=filters,
            user_id=user_id,
            session_id=session_id,
        )
