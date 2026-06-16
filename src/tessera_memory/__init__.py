"""Tessera memory service Python SDK.

>>> from tessera_memory import Tessera
>>> client = Tessera()  # reads TESSERA_API_KEY
"""

from __future__ import annotations

from . import models
from ._client import AsyncTessera, Tessera
from ._exceptions import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    TesseraError,
    UnprocessableEntityError,
    make_status_error,
)
from ._response import APIResponse
from ._version import __version__

__all__ = [
    "__version__",
    "models",
    # clients
    "Tessera",
    "AsyncTessera",
    # raw-response envelope
    "APIResponse",
    # exceptions
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
