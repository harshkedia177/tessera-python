"""Public client classes: :class:`Tessera` (sync) and :class:`AsyncTessera` (async)."""

from __future__ import annotations

from typing import Any

import httpx

from ._base_client import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncTransport,
    SyncTransport,
)
from .models import HealthStatus
from .resources.jobs import AsyncJobsResource, JobsResource
from .resources.maintenance import AsyncMaintenanceResource, MaintenanceResource
from .resources.memories import AsyncMemoriesResource, MemoriesResource
from .resources.procedures import AsyncProceduresResource, ProceduresResource
from .resources.query import AsyncQueryResource, QueryResource
from .resources.resources import AsyncResourcesResource, ResourcesResource
from .resources.search import AsyncSearchResource, SearchResource

__all__ = ["Tessera", "AsyncTessera"]

# Distinguishes an omitted with_options arg from an explicit falsy value (e.g. max_retries=0).
_NOT_GIVEN: Any = object()


class Tessera(SyncTransport):
    """Synchronous Tessera client.

    >>> client = Tessera()  # reads TESSERA_API_KEY
    >>> client.memories.add(content="...", role="user", user_id="u1")
    >>> client.search(query="...", top_k=5)
    >>> client.query(query="...", mode="chat")
    """

    memories: MemoriesResource
    jobs: JobsResource
    maintenance: MaintenanceResource
    procedures: ProceduresResource
    resources: ResourcesResource
    search: SearchResource
    query: QueryResource

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            http_client=http_client,
        )
        self.memories = MemoriesResource(self)
        self.jobs = JobsResource(self)
        self.maintenance = MaintenanceResource(self)
        self.procedures = ProceduresResource(self)
        self.resources = ResourcesResource(self)
        self.search = SearchResource(self)
        self.query = QueryResource(self)

    def with_options(
        self,
        *,
        timeout: float = _NOT_GIVEN,
        max_retries: int = _NOT_GIVEN,
        default_headers: dict[str, str] | None = _NOT_GIVEN,
    ) -> Tessera:
        """A copy with per-call overrides, sharing this client's transport."""
        merged = dict(self._default_headers)
        if default_headers is not _NOT_GIVEN and default_headers is not None:
            merged.update(default_headers)
        return Tessera(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout if timeout is _NOT_GIVEN else timeout,
            max_retries=self.max_retries if max_retries is _NOT_GIVEN else max_retries,
            default_headers=merged,
            http_client=self._http,
        )

    def health(self) -> HealthStatus:
        """Liveness probe: ``GET /health`` -> ``{"status": "ok"}``."""
        return self._request("GET", "/health", cast_to=HealthStatus)

    def ready(self) -> HealthStatus:
        """Readiness probe: ``GET /ready`` -> ``{"status": "ok"|"unavailable"}``."""
        return self._request("GET", "/ready", cast_to=HealthStatus)


class AsyncTessera(AsyncTransport):
    """Asynchronous Tessera client (mirrors :class:`Tessera` with ``await``).

    >>> client = AsyncTessera()
    >>> await client.memories.add(content="...", role="user", user_id="u1")
    >>> await client.search(query="...", top_k=5)
    >>> await client.query(query="...", mode="chat")
    """

    memories: AsyncMemoriesResource
    jobs: AsyncJobsResource
    maintenance: AsyncMaintenanceResource
    procedures: AsyncProceduresResource
    resources: AsyncResourcesResource
    search: AsyncSearchResource
    query: AsyncQueryResource

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            http_client=http_client,
        )
        self.memories = AsyncMemoriesResource(self)
        self.jobs = AsyncJobsResource(self)
        self.maintenance = AsyncMaintenanceResource(self)
        self.procedures = AsyncProceduresResource(self)
        self.resources = AsyncResourcesResource(self)
        self.search = AsyncSearchResource(self)
        self.query = AsyncQueryResource(self)

    def with_options(
        self,
        *,
        timeout: float = _NOT_GIVEN,
        max_retries: int = _NOT_GIVEN,
        default_headers: dict[str, str] | None = _NOT_GIVEN,
    ) -> AsyncTessera:
        """A copy with per-call overrides, sharing this client's transport."""
        merged = dict(self._default_headers)
        if default_headers is not _NOT_GIVEN and default_headers is not None:
            merged.update(default_headers)
        return AsyncTessera(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout if timeout is _NOT_GIVEN else timeout,
            max_retries=self.max_retries if max_retries is _NOT_GIVEN else max_retries,
            default_headers=merged,
            http_client=self._http,
        )

    async def health(self) -> HealthStatus:
        """Liveness probe: ``GET /health`` -> ``{"status": "ok"}``."""
        return await self._request("GET", "/health", cast_to=HealthStatus)

    async def ready(self) -> HealthStatus:
        """Readiness probe: ``GET /ready`` -> ``{"status": "ok"|"unavailable"}``."""
        return await self._request("GET", "/ready", cast_to=HealthStatus)
