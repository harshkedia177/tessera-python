"""Jobs resource — poll asynchronous server jobs."""

from __future__ import annotations

from .._resource import AsyncAPIResource, SyncAPIResource
from ..models import JobStatusResponse

__all__ = ["JobsResource", "AsyncJobsResource"]


class JobsResource(SyncAPIResource):
    """Poll the status of an asynchronous server job (``job_<int>``)."""

    def get(self, job_id: str) -> JobStatusResponse:
        """Fetch a job's coarse lifecycle status (``GET /v1/jobs/{job_id}``)."""
        return self._client._request(
            "GET",
            f"/v1/jobs/{job_id}",
            cast_to=JobStatusResponse,
        )


class AsyncJobsResource(AsyncAPIResource):
    """Async variant of :class:`JobsResource`."""

    async def get(self, job_id: str) -> JobStatusResponse:
        """Fetch a job's coarse lifecycle status (``GET /v1/jobs/{job_id}``)."""
        return await self._client._request(
            "GET",
            f"/v1/jobs/{job_id}",
            cast_to=JobStatusResponse,
        )
