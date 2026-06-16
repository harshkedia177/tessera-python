"""HTTP transport shared by the sync and async clients: auth, retries, and request dispatch."""

from __future__ import annotations

import logging
import os
import platform
import random
import time
from typing import TYPE_CHECKING, Any, TypeVar, cast

import httpx
from pydantic import BaseModel, TypeAdapter

from ._exceptions import (
    APIConnectionError,
    APITimeoutError,
    make_status_error,
)
from ._response import RAW_RESPONSE_MODE, APIResponse
from .models import ProblemDetail

if TYPE_CHECKING:
    from collections.abc import Mapping

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2

# A retried request can double-apply a write, so retries are gated on whether the request
# is idempotent and on *why* it failed:
#   * SAFE statuses — the server rejected the request without processing it (rate limited,
#     bad gateway, unavailable), so replaying it is safe for ANY verb.
#   * AMBIGUOUS failures — a 500 or a transport error/timeout may have been applied before
#     the failure surfaced, so we replay these ONLY for idempotent requests.
_SAFE_RETRY_STATUSES = frozenset({429, 502, 503})
_AMBIGUOUS_RETRY_STATUSES = frozenset({500})
# HTTP methods that are idempotent by definition (RFC 9110 §9.2.2).
_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "PUT", "DELETE", "OPTIONS"})
# Idempotent-write endpoint that benefits from a client-minted turn_id.
_ADD_MEMORY_PATH = "/v1/memories"

ResponseT = TypeVar("ResponseT")

# Crockford base32 alphabet used by ULID's textual encoding.
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

logger = logging.getLogger("tessera_memory")
_logging_configured = False


def _configure_logging_from_env() -> None:
    """Wire ``TESSERA_LOG`` (``debug``/``info``/…) to a stderr handler, once per process.

    No-op when the variable is unset or names an unknown level, so importing the SDK never
    changes logging behaviour unless the operator opts in.
    """
    global _logging_configured
    if _logging_configured:
        return
    _logging_configured = True

    raw = os.environ.get("TESSERA_LOG")
    if not raw:
        return
    level = getattr(logging, raw.upper(), None)
    if not isinstance(level, int):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s tessera_memory %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)


def _generate_ulid() -> str:
    """Mint a lexicographically-sortable 26-char ULID (no extra dependency).

    48-bit millisecond timestamp + 80 bits of randomness, Crockford-base32 encoded.
    Used to make a retried ``POST /v1/memories`` ``ON CONFLICT``-safe.
    """
    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    randomness = random.getrandbits(80)
    value = (timestamp_ms << 80) | randomness
    chars = [""] * 26
    for i in range(25, -1, -1):
        chars[i] = _CROCKFORD[value & 0x1F]
        value >>= 5
    return "".join(chars)


class BaseClient:
    """Auth/config resolution and sync/async-agnostic transport policy."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        _configure_logging_from_env()

        resolved_key = api_key if api_key is not None else os.environ.get("TESSERA_API_KEY")
        if not resolved_key:
            raise self._missing_api_key_error()
        self.api_key = resolved_key

        resolved_base = (
            base_url
            if base_url is not None
            else os.environ.get("TESSERA_BASE_URL") or DEFAULT_BASE_URL
        )
        self.base_url = resolved_base.rstrip("/")

        self.timeout = timeout
        self.max_retries = max_retries
        self._default_headers = dict(default_headers) if default_headers else {}

    @staticmethod
    def _missing_api_key_error() -> Exception:
        from ._exceptions import TesseraError

        return TesseraError(
            "No API key provided. Pass api_key=... to the client or set the "
            "TESSERA_API_KEY environment variable."
        )

    # -- header / request construction -------------------------------------------------

    def _build_url(self, path: str) -> str:
        """Join ``path`` onto the configured base URL.

        Requests carry the absolute URL (rather than relying on ``httpx``'s ``base_url``)
        so a caller-supplied ``http_client`` need not be configured with one.
        """
        return f"{self.base_url}{path}"

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _build_headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": self._user_agent(),
        }
        headers.update(self._auth_headers())
        headers.update(self._default_headers)
        if extra:
            headers.update(extra)
        return headers

    @staticmethod
    def _user_agent() -> str:
        """``tessera-memory-python/<ver> Python/<x.y.z> <System>/<release>`` for server logs."""
        from ._version import __version__

        return (
            f"tessera-memory-python/{__version__} "
            f"Python/{platform.python_version()} "
            f"{platform.system() or 'Unknown'}/{platform.release() or 'unknown'}"
        )

    def _prepare_json(self, method: str, path: str, json: Any) -> Any:
        """Auto-mint a ULID ``turn_id`` on memory writes when the caller omits one."""
        if (
            method.upper() == "POST"
            and path == _ADD_MEMORY_PATH
            and isinstance(json, dict)
            and not json.get("turn_id")
        ):
            return {**json, "turn_id": _generate_ulid()}
        return json

    # -- retry policy ------------------------------------------------------------------

    def _is_idempotent(self, method: str, path: str, body: Any) -> bool:
        """Whether replaying this request cannot double-apply a write.

        GET/HEAD/PUT/DELETE/OPTIONS are idempotent by definition. A ``POST`` is only
        idempotent when it carries a dedupe key the server honours — which, for this API,
        means ``POST /v1/memories`` once :meth:`_prepare_json` has minted a ``turn_id``
        (the write is then ``ON CONFLICT``-safe). Every other ``POST`` is treated as unsafe
        to replay on an ambiguous failure.
        """
        m = method.upper()
        if m in _IDEMPOTENT_METHODS:
            return True
        return (
            m == "POST"
            and path == _ADD_MEMORY_PATH
            and isinstance(body, dict)
            and bool(body.get("turn_id"))
        )

    def _should_retry_response(self, status: int, *, idempotent: bool) -> bool:
        """Retry a *response*: SAFE statuses always; AMBIGUOUS (500) only if idempotent."""
        if status in _SAFE_RETRY_STATUSES:
            return True
        if status in _AMBIGUOUS_RETRY_STATUSES:
            return idempotent
        return False

    def _retry_after_seconds(self, response: httpx.Response) -> float | None:
        """Parse a ``Retry-After`` header (delta-seconds form) into seconds."""
        value = response.headers.get("Retry-After")
        if value is None:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            return None

    def _backoff(self, attempt: int, retry_after: float | None = None) -> float:
        """Seconds to sleep before retry ``attempt`` (0-indexed): honour ``Retry-After``
        when present, else exponential backoff (0.5 * 2**attempt) capped at 8s with
        full jitter."""
        if retry_after is not None:
            return retry_after
        base: float = min(0.5 * (2.0**attempt), 8.0)
        jitter: float = 0.5 + random.random() * 0.5
        return base * jitter

    # -- response handling -------------------------------------------------------------

    @staticmethod
    def _request_id(response: httpx.Response) -> str | None:
        value = response.headers.get("X-Request-Id")
        return value if value is None else str(value)

    def _parse_problem(self, response: httpx.Response) -> ProblemDetail | None:
        try:
            payload = response.json()
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        try:
            return ProblemDetail.model_validate(payload)
        except Exception:
            return None

    def _parse_response(self, response: httpx.Response, cast_to: type[ResponseT]) -> ResponseT:
        """Return ``cast_to`` parsed from a 2xx body, or raise the mapped error.

        In raw-response mode (set by a ``with_raw_response`` proxy) the parsed model is
        wrapped in an :class:`APIResponse` alongside the status, headers, request id, and
        the underlying :class:`httpx.Response`.
        """
        if response.is_success:
            parsed = self._cast(response, cast_to)
            if RAW_RESPONSE_MODE.get():
                envelope = APIResponse(
                    parsed=parsed,
                    status_code=response.status_code,
                    headers=response.headers,
                    request_id=self._request_id(response),
                    http_response=response,
                )
                return cast("ResponseT", envelope)
            return parsed
        problem = self._parse_problem(response)
        raise make_status_error(
            response.status_code,
            problem=problem,
            request_id=self._request_id(response),
            response=response,
        )

    @staticmethod
    def _cast(response: httpx.Response, cast_to: type[ResponseT]) -> ResponseT:
        """Coerce a successful response body into ``cast_to``.

        ``None`` casts (endpoints with no body) return ``None``; Pydantic models use
        ``model_validate``; anything else is validated via a ``TypeAdapter`` so the
        common ``dict``/``list`` cases round-trip cleanly.
        """
        if cast_to is type(None):
            # Endpoints with no body cast to None; ResponseT is bound to NoneType here.
            return None
        data: Any = response.json() if response.content else None
        if isinstance(cast_to, type) and issubclass(cast_to, BaseModel):
            return cast_to.model_validate(data)
        return TypeAdapter(cast_to).validate_python(data)


class SyncTransport(BaseClient):
    """Synchronous transport: drives the retry policy over an :class:`httpx.Client`.

    The public :class:`~tessera_memory._client.Tessera` subclasses this to attach
    resource namespaces; this layer owns only the wire transport and ``_request``.

    Pass ``http_client`` to supply a pre-configured :class:`httpx.Client` (proxies, custom
    TLS, connection-pool limits, a shared transport). A client constructed that way is the
    caller's to close — :meth:`close` only tears down a transport the SDK created itself.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._owns_http = http_client is None
        self._http = http_client if http_client is not None else httpx.Client(timeout=self.timeout)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
        files: Any | None = None,
        cast_to: type[ResponseT],
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> ResponseT:
        body = self._prepare_json(method, path, json)
        headers = self._build_headers()
        url = self._build_url(path)
        retries = self.max_retries if max_retries is None else max_retries
        request_timeout: Any = self.timeout if timeout is None else timeout
        idempotent = self._is_idempotent(method, path, body)
        last_exc: Exception | None = None

        for attempt in range(retries + 1):
            logger.debug("request %s %s (attempt %d/%d)", method, url, attempt + 1, retries + 1)
            try:
                response = self._http.request(
                    method,
                    url,
                    json=body if files is None else None,
                    params=params,
                    files=files,
                    data=body if files is not None and isinstance(body, dict) else None,
                    headers=headers,
                    timeout=request_timeout,
                )
            except httpx.TimeoutException as exc:
                last_exc = APITimeoutError(request=exc.request)
                if attempt < retries and idempotent:
                    delay = self._backoff(attempt)
                    logger.debug("timeout on %s %s; retrying in %.2fs", method, url, delay)
                    time.sleep(delay)
                    continue
                raise last_exc from exc
            except httpx.TransportError as exc:
                last_exc = APIConnectionError(request=exc.request)
                if attempt < retries and idempotent:
                    delay = self._backoff(attempt)
                    logger.debug("connection error on %s %s; retrying in %.2fs", method, url, delay)
                    time.sleep(delay)
                    continue
                raise last_exc from exc

            logger.debug("response %s %s -> %d", method, url, response.status_code)
            if attempt < retries and self._should_retry_response(
                response.status_code, idempotent=idempotent
            ):
                delay = self._backoff(attempt, self._retry_after_seconds(response))
                logger.debug(
                    "retryable status %d on %s %s; retrying in %.2fs",
                    response.status_code,
                    method,
                    url,
                    delay,
                )
                time.sleep(delay)
                continue

            return self._parse_response(response, cast_to)

        # Unreachable: the loop returns or raises on every path. Guard for the type checker.
        raise last_exc or APIConnectionError()

    def close(self) -> None:
        """Close the transport — unless it was supplied by the caller."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> SyncTransport:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class AsyncTransport(BaseClient):
    """Asynchronous transport: drives the retry policy over an :class:`httpx.AsyncClient`.

    The public :class:`~tessera_memory._client.AsyncTessera` subclasses this to attach
    resource namespaces; this layer owns only the wire transport and ``_request``.

    Pass ``http_client`` to supply a pre-configured :class:`httpx.AsyncClient`. A client
    supplied that way is the caller's to close — :meth:`aclose` only tears down a transport
    the SDK created itself.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._owns_http = http_client is None
        self._http = (
            http_client if http_client is not None else httpx.AsyncClient(timeout=self.timeout)
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
        files: Any | None = None,
        cast_to: type[ResponseT],
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> ResponseT:
        import asyncio

        body = self._prepare_json(method, path, json)
        headers = self._build_headers()
        url = self._build_url(path)
        retries = self.max_retries if max_retries is None else max_retries
        request_timeout: Any = self.timeout if timeout is None else timeout
        idempotent = self._is_idempotent(method, path, body)
        last_exc: Exception | None = None

        for attempt in range(retries + 1):
            logger.debug("request %s %s (attempt %d/%d)", method, url, attempt + 1, retries + 1)
            try:
                response = await self._http.request(
                    method,
                    url,
                    json=body if files is None else None,
                    params=params,
                    files=files,
                    data=body if files is not None and isinstance(body, dict) else None,
                    headers=headers,
                    timeout=request_timeout,
                )
            except httpx.TimeoutException as exc:
                last_exc = APITimeoutError(request=exc.request)
                if attempt < retries and idempotent:
                    delay = self._backoff(attempt)
                    logger.debug("timeout on %s %s; retrying in %.2fs", method, url, delay)
                    await asyncio.sleep(delay)
                    continue
                raise last_exc from exc
            except httpx.TransportError as exc:
                last_exc = APIConnectionError(request=exc.request)
                if attempt < retries and idempotent:
                    delay = self._backoff(attempt)
                    logger.debug("connection error on %s %s; retrying in %.2fs", method, url, delay)
                    await asyncio.sleep(delay)
                    continue
                raise last_exc from exc

            logger.debug("response %s %s -> %d", method, url, response.status_code)
            if attempt < retries and self._should_retry_response(
                response.status_code, idempotent=idempotent
            ):
                delay = self._backoff(attempt, self._retry_after_seconds(response))
                logger.debug(
                    "retryable status %d on %s %s; retrying in %.2fs",
                    response.status_code,
                    method,
                    url,
                    delay,
                )
                await asyncio.sleep(delay)
                continue

            return self._parse_response(response, cast_to)

        raise last_exc or APIConnectionError()

    async def aclose(self) -> None:
        """Close the transport — unless it was supplied by the caller."""
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()
