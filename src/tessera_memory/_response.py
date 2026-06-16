"""Raw-response escape hatch exposing transport metadata via ``with_raw_response``."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx

# When truthy, ``_request`` returns an ``APIResponse``; a ContextVar to stay concurrency-safe.
RAW_RESPONSE_MODE: ContextVar[bool] = ContextVar("tessera_raw_response_mode", default=False)


@dataclass(frozen=True)
class APIResponse:
    """A parsed result paired with its transport-level metadata."""

    parsed: Any
    status_code: int
    headers: httpx.Headers
    request_id: str | None
    http_response: httpx.Response
