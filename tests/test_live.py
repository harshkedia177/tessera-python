"""Live end-to-end suite against a real Tessera server — exercises EVERY public method.

Skipped by default: the ``live`` marker is deselected in ``conftest`` unless ``--run-live``
is passed, and each test additionally skips when ``TESSERA_API_KEY`` is unset. Run with::

    TESSERA_BASE_URL=https://your-server TESSERA_API_KEY=tsk_live_... \\
        uv run pytest --run-live -q

The full suite assumes a server with provider keys wired (Gemini embeddings + an LLM for
consolidation/query, and a VLM for ``resources.file``). ``test_live_round_trip`` is the only
test that works without provider keys (it uses ``infer=False``).

State flows through a module-scoped fixture (``sync_ctx``) that seeds a unique throwaway user
once and wipes it on teardown; destructive-op tests are scoped so they do not clobber each other.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest

from tessera_memory import AsyncTessera, AuthenticationError, NotFoundError, Tessera

pytestmark = pytest.mark.live

_REQUIRES_ENV = pytest.mark.skipif(
    not os.environ.get("TESSERA_API_KEY"),
    reason="TESSERA_API_KEY not set; live tests require a real server + key.",
)

_FACTS = [
    "My name is Dana Okafor.",
    "I live in Berlin, Germany.",
    "My favorite color is teal.",
    "I work as a marine biologist.",
    "I drink oolong tea every morning.",
    "I love scuba diving on the weekends.",
    "My partner's name is Sam.",
    "I drive a blue Volkswagen.",
]


def _ids(model: object, prefix: str) -> list[str]:
    out: list[str] = []

    def rec(o: object) -> None:
        if isinstance(o, dict):
            for v in o.values():
                rec(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                rec(v)
        elif isinstance(o, str) and o.startswith(prefix):
            out.append(o)

    rec(model.model_dump() if hasattr(model, "model_dump") else model)
    return out


@_REQUIRES_ENV
def test_live_round_trip() -> None:
    """Liveness + an ``infer=False`` write read back via ``list`` — no provider keys needed."""
    client = Tessera()
    try:
        assert client.health().status.value == "ok"
        added = client.memories.add(
            content="The SDK live smoke ran.",
            role="user",
            user_id="sdk-live-smoke",
            infer=False,
            mode="async",
        )
        assert added.turn_id
        page = client.memories.list(user_id="sdk-live-smoke", limit=5)
        assert isinstance(page.items, list)
    finally:
        client.close()


@pytest.fixture(scope="module")
def sync_ctx() -> Iterator[SimpleNamespace]:
    if not os.environ.get("TESSERA_API_KEY"):
        pytest.skip("TESSERA_API_KEY not set; live suite requires a real server + key.")
    client = Tessera()
    user = f"sdk-live-{uuid.uuid4().hex[:8]}"

    async_add = client.memories.add(content=_FACTS[0], role="user", user_id=user, mode="async")
    for text in _FACTS[1:]:
        client.memories.add(content=text, role="user", user_id=user, mode="sync")
    time.sleep(2)  # let any queued consolidation settle

    items = list(client.memories.list(user_id=user, limit=50))
    ep_ids = [i.id for i in items if i.id.startswith("ep_")]
    facts = client.search(
        query="name color city job partner car", user_id=user, top_k=25, types=["fact"]
    )
    ft_ids = _ids(facts, "ft_")
    enqueued = client.maintenance.consolidate(user_id=user)
    job_ids = _ids(enqueued, "job_")

    ctx = SimpleNamespace(
        client=client,
        user=user,
        ep_ids=ep_ids,
        ft_ids=ft_ids,
        async_turn_id=async_add.turn_id,
        job_ids=job_ids,
    )
    try:
        yield ctx
    finally:
        client.memories.wipe(user_id=user)
        client.close()


def test_health(sync_ctx: SimpleNamespace) -> None:
    assert sync_ctx.client.health().status.value == "ok"


def test_ready(sync_ctx: SimpleNamespace) -> None:
    assert sync_ctx.client.ready().status.value == "ok"


def test_add_async_minted_turn_id(sync_ctx: SimpleNamespace) -> None:
    assert sync_ctx.async_turn_id and len(sync_ctx.async_turn_id) == 26  # ULID


def test_add_sync_consolidated_into_episodes(sync_ctx: SimpleNamespace) -> None:
    assert sync_ctx.ep_ids, "sync adds should have consolidated into at least one ep_ episode"


def test_batch(sync_ctx: SimpleNamespace) -> None:
    resp = sync_ctx.client.memories.batch(
        messages=[
            {"role": "user", "content": "I have a dog named Pixel."},
            {"role": "user", "content": "Pixel is a corgi."},
        ],
        user_id=sync_ctx.user,
    )
    assert len(resp.results) == 2


def test_get(sync_ctx: SimpleNamespace) -> None:
    got = sync_ctx.client.memories.get(sync_ctx.ep_ids[0], user_id=sync_ctx.user)
    assert got.id == sync_ctx.ep_ids[0]


def test_search(sync_ctx: SimpleNamespace) -> None:
    resp = sync_ctx.client.search(query="favorite color", user_id=sync_ctx.user, top_k=10)
    assert resp.results and all(r.id and r.type for r in resp.results)


def test_search_typed_facts(sync_ctx: SimpleNamespace) -> None:
    resp = sync_ctx.client.search(
        query="name city job", user_id=sync_ctx.user, top_k=20, types=["fact"]
    )
    assert isinstance(resp.results, list)


def test_correct(sync_ctx: SimpleNamespace) -> None:
    if not sync_ctx.ft_ids:
        pytest.skip("no ft_ fact materialized to correct")
    new_edge = sync_ctx.client.memories.correct(
        sync_ctx.ft_ids[0], object="cyan", user_id=sync_ctx.user
    )
    assert new_edge.id.startswith("ft_")


def test_pin_unpin(sync_ctx: SimpleNamespace) -> None:
    ep = sync_ctx.ep_ids[0]
    assert sync_ctx.client.memories.pin(ep, user_id=sync_ctx.user).pinned is True
    assert sync_ctx.client.memories.unpin(ep, user_id=sync_ctx.user).pinned is False


def test_query_chat(sync_ctx: SimpleNamespace) -> None:
    resp = sync_ctx.client.query(
        query="What is my favorite color?", mode="chat", user_id=sync_ctx.user
    )
    assert resp.context


def test_query_reasoning(sync_ctx: SimpleNamespace) -> None:
    resp = sync_ctx.client.query(
        query="Where do I live and work?", mode="reasoning", user_id=sync_ctx.user
    )
    assert resp.context


def test_maintenance_consolidate(sync_ctx: SimpleNamespace) -> None:
    assert sync_ctx.client.maintenance.consolidate(user_id=sync_ctx.user) is not None


def test_maintenance_reindex(sync_ctx: SimpleNamespace) -> None:
    assert sync_ctx.client.maintenance.reindex(user_id=sync_ctx.user) is not None


def test_maintenance_compress(sync_ctx: SimpleNamespace) -> None:
    assert (
        sync_ctx.client.maintenance.compress(user_id=sync_ctx.user, token_budget=2000) is not None
    )


def test_jobs_get(sync_ctx: SimpleNamespace) -> None:
    if not sync_ctx.job_ids:
        pytest.skip("no job_ id produced to fetch")
    assert sync_ctx.client.jobs.get(sync_ctx.job_ids[0]).status is not None


def test_procedures_lifecycle(sync_ctx: SimpleNamespace) -> None:
    c, user = sync_ctx.client, sync_ctx.user
    proc = c.procedures.remember(
        trigger="user asks to reset their password",
        steps=["open settings", "click security", "click reset password"],
        success="the password is changed",
        user_id=user,
    )
    assert proc.id
    c.procedures.recall(task="how do I reset my password", user_id=user)
    assert c.procedures.record_outcome(proc.id, success=True, user_id=user) is not None


def test_resources_lifecycle(sync_ctx: SimpleNamespace, tmp_path: Path) -> None:
    import struct
    import zlib

    c, user = sync_ctx.client, sync_ctx.user
    res = c.resources.remember(
        blob_ref="blob://teal", mime="image/png", caption="a teal square", user_id=user
    )
    assert res.id

    img = tmp_path / "teal.png"
    raw = (b"\x00" + bytes((0, 128, 128, 255)) * 8) * 8

    def _chunk(typ: bytes, data: bytes) -> bytes:
        c2 = typ + data
        return struct.pack(">I", len(data)) + c2 + struct.pack(">I", zlib.crc32(c2) & 0xFFFFFFFF)

    img.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 6, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )
    uploaded = c.resources.file(path=img, blob_ref="blob://upload", user_id=user)
    assert uploaded.id  # the MIME must be inferred to image/png or the server 422s
    assert c.resources.recall(query="teal square", user_id=user) is not None


def test_forget_turn(sync_ctx: SimpleNamespace) -> None:
    """Add a fresh turn, then forget it — scoped so it touches only its own turn."""
    c, user = sync_ctx.client, sync_ctx.user
    added = c.memories.add(
        content="A disposable turn to forget.", role="user", user_id=user, infer=False
    )
    resp = c.memories.forget_turn(added.turn_id, user_id=user)
    assert resp.turns_deleted >= 1


def test_delete(sync_ctx: SimpleNamespace) -> None:
    """Delete the LAST seeded episode (reads use ep_ids[0], so this is safe)."""
    resp = sync_ctx.client.memories.delete(sync_ctx.ep_ids[-1], user_id=sync_ctx.user)
    assert resp is not None


def test_wipe_isolated_user() -> None:
    """Wipe is destructive, so it runs against its OWN throwaway user."""
    c = Tessera()
    user = f"sdk-live-wipe-{uuid.uuid4().hex[:8]}"
    try:
        c.memories.add(content="ephemeral 1", role="user", user_id=user, infer=False)
        c.memories.add(content="ephemeral 2", role="user", user_id=user, infer=False)
        assert c.memories.wipe(user_id=user).total >= 2
    finally:
        c.close()


@_REQUIRES_ENV
def test_error_authentication() -> None:
    c = Tessera(api_key="tsk_live_definitely_not_a_real_key_000")
    with pytest.raises(AuthenticationError) as exc:
        c.memories.list(user_id="whoever")
    assert exc.value.status_code == 401
    c.close()


def test_error_not_found(sync_ctx: SimpleNamespace) -> None:
    with pytest.raises(NotFoundError) as exc:
        sync_ctx.client.memories.get(
            "ep_00000000-0000-0000-0000-000000000000", user_id=sync_ctx.user
        )
    assert exc.value.status_code == 404


@_REQUIRES_ENV
async def test_async_lifecycle() -> None:
    client = AsyncTessera()
    user = f"sdk-live-async-{uuid.uuid4().hex[:8]}"
    try:
        assert (await client.health()).status.value == "ok"
        assert (await client.ready()).status.value == "ok"

        for text in _FACTS[:5]:
            await client.memories.add(content=text, role="user", user_id=user, mode="sync")
        async_add = await client.memories.add(
            content="async turn", role="user", user_id=user, mode="async"
        )
        assert async_add.turn_id

        batch = await client.memories.batch(
            messages=[{"role": "user", "content": "a"}, {"role": "user", "content": "b"}],
            user_id=user,
        )
        assert len(batch.results) == 2

        page = await client.memories.list(user_id=user, limit=50)
        items = [item async for item in page]  # exercise async iteration / pagination
        ep_ids = [i.id for i in items if i.id.startswith("ep_")]
        assert ep_ids

        got = await client.memories.get(ep_ids[0], user_id=user)
        assert got.id == ep_ids[0]
        assert (await client.memories.pin(ep_ids[0], user_id=user)).pinned is True
        assert (await client.memories.unpin(ep_ids[0], user_id=user)).pinned is False

        assert (
            await client.search(query="favorite color", user_id=user, top_k=5)
        ).results is not None
        facts = await client.search(query="name city job", user_id=user, top_k=20, types=["fact"])
        ft_ids = _ids(facts, "ft_")
        if ft_ids:
            assert (
                await client.memories.correct(ft_ids[0], object="cyan", user_id=user)
            ).id.startswith("ft_")

        assert (
            await client.query(query="What is my favorite color?", mode="chat", user_id=user)
        ).context
        assert (
            await client.query(query="Where do I live?", mode="reasoning", user_id=user)
        ).context

        enq = await client.maintenance.consolidate(user_id=user)
        job_ids = _ids(enq, "job_")
        assert (await client.maintenance.reindex(user_id=user)) is not None
        assert (await client.maintenance.compress(user_id=user, token_budget=2000)) is not None
        if job_ids:
            assert (await client.jobs.get(job_ids[0])).status is not None

        proc = await client.procedures.remember(
            trigger="user wants to export data",
            steps=["go to account", "click export"],
            success="a download starts",
            user_id=user,
        )
        assert proc.id
        await client.procedures.recall(task="export my data", user_id=user)
        assert (
            await client.procedures.record_outcome(proc.id, success=False, user_id=user)
        ) is not None

        res = await client.resources.remember(
            blob_ref="blob://a", mime="image/png", caption="x", user_id=user
        )
        assert res.id
        assert (await client.resources.recall(query="teal", user_id=user)) is not None

        forgot = await client.memories.forget_turn(async_add.turn_id, user_id=user)
        assert forgot is not None
        assert (await client.memories.delete(ep_ids[-1], user_id=user)) is not None
        assert (await client.memories.wipe(user_id=user)).total >= 0
    finally:
        await client.aclose()
