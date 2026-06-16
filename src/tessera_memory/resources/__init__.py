"""Resource namespaces for the Tessera SDK."""

from __future__ import annotations

from .jobs import AsyncJobsResource, JobsResource
from .maintenance import AsyncMaintenanceResource, MaintenanceResource
from .memories import AsyncMemoriesResource, MemoriesResource
from .procedures import AsyncProceduresResource, ProceduresResource
from .query import AsyncQueryResource, QueryResource
from .resources import AsyncResourcesResource, ResourcesResource
from .search import AsyncSearchResource, SearchResource

__all__ = [
    "MemoriesResource",
    "AsyncMemoriesResource",
    "SearchResource",
    "AsyncSearchResource",
    "QueryResource",
    "AsyncQueryResource",
    "JobsResource",
    "AsyncJobsResource",
    "MaintenanceResource",
    "AsyncMaintenanceResource",
    "ProceduresResource",
    "AsyncProceduresResource",
    "ResourcesResource",
    "AsyncResourcesResource",
]
