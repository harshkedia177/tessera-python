"""Base classes for resource namespaces."""

from __future__ import annotations

import functools
import inspect
from typing import TYPE_CHECKING, Any

from ._response import RAW_RESPONSE_MODE

if TYPE_CHECKING:
    from ._client import AsyncTessera, Tessera


class _RawResponseProxy:
    """Wraps a resource so its methods return :class:`APIResponse`."""

    def __init__(self, resource: object) -> None:
        self._resource = resource

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._resource, name)
        if not callable(attr):
            return attr

        if inspect.iscoroutinefunction(attr):

            @functools.wraps(attr)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                token = RAW_RESPONSE_MODE.set(True)
                try:
                    return await attr(*args, **kwargs)
                finally:
                    RAW_RESPONSE_MODE.reset(token)

            return async_wrapper

        @functools.wraps(attr)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            token = RAW_RESPONSE_MODE.set(True)
            try:
                return attr(*args, **kwargs)
            finally:
                RAW_RESPONSE_MODE.reset(token)

        return wrapper


class SyncAPIResource:
    """Base for synchronous resource namespaces."""

    def __init__(self, client: Tessera) -> None:
        self._client = client

    @property
    def with_raw_response(self) -> Any:
        """Same methods, but each returns an :class:`APIResponse` (parsed + metadata)."""
        return _RawResponseProxy(self)


class AsyncAPIResource:
    """Base for asynchronous resource namespaces."""

    def __init__(self, client: AsyncTessera) -> None:
        self._client = client

    @property
    def with_raw_response(self) -> Any:
        """Same methods, but each returns an :class:`APIResponse` (parsed + metadata)."""
        return _RawResponseProxy(self)
