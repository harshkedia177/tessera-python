"""Pure tool handlers: map MCP tool args to Tessera SDK calls, return text."""

from __future__ import annotations

from tessera_memory import AsyncTessera


async def recall(
    client: AsyncTessera, *, query: str, user_id: str, session_id: str | None = None
) -> str:
    """Composed, prompt-ready memory context for the repo/task."""
    resp = await client.query(query=query, mode="chat", user_id=user_id, session_id=session_id)
    return resp.context or "(no relevant memory found)"


async def search(
    client: AsyncTessera, *, query: str, user_id: str, session_id: str | None = None
) -> str:
    """Raw hybrid search hits (no LLM)."""
    resp = await client.search(query=query, top_k=10, user_id=user_id, session_id=session_id)
    if not resp.results:
        return "(no results)"
    return "\n".join(f"- [{r.type}] {r.text} (score {r.score:.2f})" for r in resp.results)


async def save_lesson(
    client: AsyncTessera,
    *,
    trigger: str,
    steps: list[str],
    success: str,
    user_id: str,
    session_id: str | None = None,
) -> str:
    """Store a reusable lesson / how-to as a procedural memory."""
    proc = await client.procedures.remember(
        trigger=trigger, steps=steps, success=success, user_id=user_id, session_id=session_id
    )
    return f"Saved lesson {proc.id}: {proc.trigger}"


async def recall_lessons(
    client: AsyncTessera, *, situation: str, user_id: str, session_id: str | None = None
) -> str:
    """Fetch lessons matching a situation."""
    resp = await client.procedures.recall(task=situation, user_id=user_id, session_id=session_id)
    if not resp.results:
        return "(no matching lessons)"
    lines: list[str] = []
    for r in resp.results:
        p = r.procedure
        lines.append(
            f"- {p.trigger} (sim {r.similarity:.2f})\n"
            f"  steps: {'; '.join(p.steps)}\n"
            f"  success: {p.success}"
        )
    return "\n".join(lines)


async def note(
    client: AsyncTessera, *, text: str, user_id: str, session_id: str | None = None
) -> str:
    """Store a durable repo convention without consolidation."""
    resp = await client.memories.add(
        content=text, role="user", user_id=user_id, session_id=session_id, infer=False
    )
    return f"Noted (turn {resp.turn_id})."
