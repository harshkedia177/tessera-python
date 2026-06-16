"""Maintenance resource — trigger consolidation, reindex, and compression jobs."""

from __future__ import annotations

from typing import cast

from .._resource import AsyncAPIResource, SyncAPIResource
from ..models import (
    CompressRequest,
    CompressResponse,
    ConsolidateRequest,
    EnqueuedResponse,
    ReindexResponse,
    TesseraApiV1MaintenanceConsolidationSummary,
)

# consolidate returns a 200 summary or 202 enqueued; cast names the runtime union for mypy.
_ConsolidateResult = TesseraApiV1MaintenanceConsolidationSummary | EnqueuedResponse
_CONSOLIDATE_CAST = cast(
    "type[_ConsolidateResult]",
    TesseraApiV1MaintenanceConsolidationSummary | EnqueuedResponse,
)

__all__ = ["MaintenanceResource", "AsyncMaintenanceResource"]


class MaintenanceResource(SyncAPIResource):
    """Trigger consolidation, reindex, and compression maintenance jobs."""

    def consolidate(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> TesseraApiV1MaintenanceConsolidationSummary | EnqueuedResponse:
        """Run memory consolidation over a partition (``POST /v1/consolidate``)."""
        req = ConsolidateRequest(user_id=user_id, session_id=session_id)
        return self._client._request(
            "POST",
            "/v1/consolidate",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=_CONSOLIDATE_CAST,
        )

    def reindex(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ReindexResponse:
        """Rebuild derived indexes for a partition (``POST /v1/reindex``)."""
        req = ConsolidateRequest(user_id=user_id, session_id=session_id)
        return self._client._request(
            "POST",
            "/v1/reindex",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=ReindexResponse,
        )

    def compress(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        token_budget: int | None = None,
    ) -> CompressResponse:
        """Pack a partition's memory into a token-budgeted digest (``POST /v1/compress``)."""
        req = CompressRequest(
            user_id=user_id,
            session_id=session_id,
            token_budget=token_budget,
        )
        return self._client._request(
            "POST",
            "/v1/compress",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=CompressResponse,
        )


class AsyncMaintenanceResource(AsyncAPIResource):
    """Async variant of :class:`MaintenanceResource`."""

    async def consolidate(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> TesseraApiV1MaintenanceConsolidationSummary | EnqueuedResponse:
        """Run memory consolidation over a partition (``POST /v1/consolidate``)."""
        req = ConsolidateRequest(user_id=user_id, session_id=session_id)
        return await self._client._request(
            "POST",
            "/v1/consolidate",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=_CONSOLIDATE_CAST,
        )

    async def reindex(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ReindexResponse:
        """Rebuild derived indexes for a partition (``POST /v1/reindex``)."""
        req = ConsolidateRequest(user_id=user_id, session_id=session_id)
        return await self._client._request(
            "POST",
            "/v1/reindex",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=ReindexResponse,
        )

    async def compress(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        token_budget: int | None = None,
    ) -> CompressResponse:
        """Pack a partition's memory into a token-budgeted digest (``POST /v1/compress``)."""
        req = CompressRequest(
            user_id=user_id,
            session_id=session_id,
            token_budget=token_budget,
        )
        return await self._client._request(
            "POST",
            "/v1/compress",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=CompressResponse,
        )
