"""Keyset auto-pagers that follow ``next_cursor`` across the server's paged list shape."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Generic, TypeVar

T = TypeVar("T")

SyncFetchNext = Callable[[str], "SyncCursorPage[T]"]
AsyncFetchNext = Callable[[str], Awaitable["AsyncCursorPage[T]"]]


class SyncCursorPage(Generic[T]):
    """One page of results; iterates across page boundaries by following the cursor."""

    def __init__(
        self,
        *,
        items: list[T],
        next_cursor: str | None,
        has_more: bool,
        fetch_next: SyncFetchNext[T],
    ) -> None:
        self.items = items
        self.next_cursor = next_cursor
        self.has_more = has_more
        self._fetch_next = fetch_next

    def has_next_page(self) -> bool:
        """Whether a further page exists *and* a cursor is available to fetch it."""
        return self.has_more and self.next_cursor is not None

    def get_next_page(self) -> SyncCursorPage[T]:
        """Fetch the page following this one. Raises if there is no next page."""
        if not self.has_next_page() or self.next_cursor is None:
            raise RuntimeError("No next page: has_more is false or next_cursor is missing.")
        return self._fetch_next(self.next_cursor)

    def iter_pages(self) -> Iterator[SyncCursorPage[T]]:
        """Yield this page, then each subsequent page, following the cursor."""
        page: SyncCursorPage[T] = self
        while True:
            yield page
            if not page.has_next_page():
                return
            page = page.get_next_page()

    def __iter__(self) -> Iterator[T]:
        """Yield every item across all pages, auto-following ``next_cursor``."""
        for page in self.iter_pages():
            yield from page.items


class AsyncCursorPage(Generic[T]):
    """Async analogue of :class:`SyncCursorPage`."""

    def __init__(
        self,
        *,
        items: list[T],
        next_cursor: str | None,
        has_more: bool,
        fetch_next: AsyncFetchNext[T],
    ) -> None:
        self.items = items
        self.next_cursor = next_cursor
        self.has_more = has_more
        self._fetch_next = fetch_next

    def has_next_page(self) -> bool:
        """Whether a further page exists *and* a cursor is available to fetch it."""
        return self.has_more and self.next_cursor is not None

    async def get_next_page(self) -> AsyncCursorPage[T]:
        """Fetch the page following this one. Raises if there is no next page."""
        if not self.has_next_page() or self.next_cursor is None:
            raise RuntimeError("No next page: has_more is false or next_cursor is missing.")
        return await self._fetch_next(self.next_cursor)

    async def iter_pages(self) -> AsyncIterator[AsyncCursorPage[T]]:
        """Yield this page, then each subsequent page, following the cursor."""
        page: AsyncCursorPage[T] = self
        while True:
            yield page
            if not page.has_next_page():
                return
            page = await page.get_next_page()

    async def __aiter__(self) -> AsyncIterator[T]:
        """Yield every item across all pages, auto-following ``next_cursor``."""
        async for page in self.iter_pages():
            for item in page.items:
                yield item
