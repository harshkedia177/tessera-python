"""Typed exception hierarchy mapping HTTP status codes onto ``except``-able SDK errors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import ProblemDetail

if TYPE_CHECKING:
    import httpx

__all__ = [
    "TesseraError",
    "APIConnectionError",
    "APITimeoutError",
    "APIError",
    "APIStatusError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
    "make_status_error",
]


class TesseraError(Exception):
    """Base class for every error raised by the SDK."""


class APIConnectionError(TesseraError):
    """The request never produced an HTTP response (DNS, TCP, TLS, dropped socket)."""

    def __init__(
        self,
        message: str = "Connection error.",
        *,
        request: httpx.Request | None = None,
    ) -> None:
        super().__init__(message)
        self.request = request


class APITimeoutError(APIConnectionError):
    """The request timed out before the server responded."""

    def __init__(self, *, request: httpx.Request | None = None) -> None:
        super().__init__("Request timed out.", request=request)


class APIError(TesseraError):
    """The server produced an HTTP response (a status code was seen)."""

    status_code: int
    problem: ProblemDetail | None
    request_id: str | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        problem: ProblemDetail | None = None,
        request_id: str | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.problem = problem
        self.request_id = request_id
        self.response = response


class APIStatusError(APIError):
    """A non-2xx HTTP status carrying (when present) a parsed ``ProblemDetail``."""


class AuthenticationError(APIStatusError):
    """401 — the API key is missing, malformed, or rejected."""


class PermissionDeniedError(APIStatusError):
    """403 — the key is valid but not allowed to perform this operation."""


class NotFoundError(APIStatusError):
    """404 — the addressed resource does not exist."""


class ConflictError(APIStatusError):
    """409 — the request conflicts with the current state of the resource."""


class UnprocessableEntityError(APIStatusError):
    """422 — the request was well-formed but semantically invalid."""


class RateLimitError(APIStatusError):
    """429 — too many requests; honour ``Retry-After`` and back off."""


class InternalServerError(APIStatusError):
    """>= 500 — the server failed to fulfil an apparently valid request."""


_STATUS_TO_ERROR: dict[int, type[APIStatusError]] = {
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


def make_status_error(
    status: int,
    *,
    problem: ProblemDetail | None,
    request_id: str | None,
    response: httpx.Response | None,
) -> APIStatusError:
    """Build the most specific :class:`APIStatusError` for ``status``."""
    if status >= 500:
        error_cls: type[APIStatusError] = InternalServerError
    else:
        error_cls = _STATUS_TO_ERROR.get(status, APIStatusError)

    if problem is not None and problem.detail:
        message = problem.detail
    elif problem is not None and problem.title:
        message = problem.title
    else:
        message = f"Tessera API returned status {status}."

    return error_cls(
        message,
        status_code=status,
        problem=problem,
        request_id=request_id,
        response=response,
    )
