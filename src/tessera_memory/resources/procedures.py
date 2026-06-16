"""Procedures resource — remember, recall, and reinforce procedural ("how-to") memories."""

from __future__ import annotations

from .._resource import AsyncAPIResource, SyncAPIResource
from ..models import (
    ProcedureView,
    RecallProceduresRequest,
    RecallProceduresResponse,
    RecordOutcomeRequest,
    RememberProcedureRequest,
)

__all__ = ["ProceduresResource", "AsyncProceduresResource"]


class ProceduresResource(SyncAPIResource):
    """Remember, recall, and score procedural ("how-to") memories."""

    def remember(
        self,
        *,
        trigger: str,
        steps: list[str],
        success: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ProcedureView:
        """Store a how-to skill recallable by trigger similarity (``POST /v1/procedures``)."""
        req = RememberProcedureRequest(
            trigger=trigger,
            steps=steps,
            success=success,
            user_id=user_id,
            session_id=session_id,
        )
        return self._client._request(
            "POST",
            "/v1/procedures",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=ProcedureView,
        )

    def recall(
        self,
        *,
        task: str,
        k: int | None = None,
        min_similarity: float | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> RecallProceduresResponse:
        """Recall learned skills whose trigger best matches a task (``POST /v1/procedures/recall``).

        A read — it does not touch use counts.
        """
        req = RecallProceduresRequest(
            task=task,
            k=k,
            min_similarity=min_similarity,
            user_id=user_id,
            session_id=session_id,
        )
        return self._client._request(
            "POST",
            "/v1/procedures/recall",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=RecallProceduresResponse,
        )

    def record_outcome(
        self,
        item_id: str,
        *,
        success: bool,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ProcedureView:
        """Record a procedure outcome, updating its reinforcement state.

        ``POST /v1/procedures/{item_id}/outcome``. A failure still counts as a use.
        """
        req = RecordOutcomeRequest(
            success=success,
            user_id=user_id,
            session_id=session_id,
        )
        return self._client._request(
            "POST",
            f"/v1/procedures/{item_id}/outcome",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=ProcedureView,
        )


class AsyncProceduresResource(AsyncAPIResource):
    """Async variant of :class:`ProceduresResource`."""

    async def remember(
        self,
        *,
        trigger: str,
        steps: list[str],
        success: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ProcedureView:
        """Store a how-to skill recallable by trigger similarity (``POST /v1/procedures``)."""
        req = RememberProcedureRequest(
            trigger=trigger,
            steps=steps,
            success=success,
            user_id=user_id,
            session_id=session_id,
        )
        return await self._client._request(
            "POST",
            "/v1/procedures",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=ProcedureView,
        )

    async def recall(
        self,
        *,
        task: str,
        k: int | None = None,
        min_similarity: float | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> RecallProceduresResponse:
        """Recall learned skills whose trigger best matches a task (``POST /v1/procedures/recall``).

        A read — it does not touch use counts.
        """
        req = RecallProceduresRequest(
            task=task,
            k=k,
            min_similarity=min_similarity,
            user_id=user_id,
            session_id=session_id,
        )
        return await self._client._request(
            "POST",
            "/v1/procedures/recall",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=RecallProceduresResponse,
        )

    async def record_outcome(
        self,
        item_id: str,
        *,
        success: bool,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> ProcedureView:
        """Record a procedure outcome, updating its reinforcement state.

        ``POST /v1/procedures/{item_id}/outcome``. A failure still counts as a use.
        """
        req = RecordOutcomeRequest(
            success=success,
            user_id=user_id,
            session_id=session_id,
        )
        return await self._client._request(
            "POST",
            f"/v1/procedures/{item_id}/outcome",
            json=req.model_dump(mode="json", exclude_none=True),
            cast_to=ProcedureView,
        )
