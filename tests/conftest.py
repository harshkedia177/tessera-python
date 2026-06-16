from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator

import pytest

from _helpers import API_KEY, BASE_URL
from tessera_memory import AsyncTessera, Tessera


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run the @pytest.mark.live end-to-end smoke against a real server.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-live"):
        return
    skip_live = pytest.mark.skip(reason="live smoke skipped by default; pass --run-live")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture
def client() -> Iterator[Tessera]:
    c = Tessera(api_key=API_KEY, base_url=BASE_URL)
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
async def async_client() -> AsyncTessera:
    return AsyncTessera(api_key=API_KEY, base_url=BASE_URL)


@pytest.fixture
def recorded_sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    delays: list[float] = []

    def fake_sleep(seconds: float) -> None:
        delays.append(seconds)

    async def fake_async_sleep(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr(time, "sleep", fake_sleep)
    monkeypatch.setattr(asyncio, "sleep", fake_async_sleep)
    return delays
