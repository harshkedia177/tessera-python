"""FastMCP server exposing Tessera memory tools over stdio."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from tessera_memory import AsyncTessera

from . import tools
from .config import Config
from .credentials import load_api_key

# Returned by every tool when no key is configured: tells the agent exactly how to fix it
# (ask the user, then run login) instead of failing with an opaque 401.
NO_KEY_MESSAGE = (
    "No Tessera API key is configured. Ask the user for their Tessera API key (it starts "
    "with 'tsk_live_'), then run this once in a terminal:\n"
    "    uvx --from tessera-mcp tessera-mcp login <key>\n"
    "It is saved to ~/.tessera/credentials.json and every repo picks it up automatically — "
    "the next memory call will work without restarting."
)


def build_server(config: Config | None = None) -> FastMCP:
    config = config or Config.from_env()
    mcp = FastMCP("tessera_memory")

    # Build the client lazily and cache it, rebuilding only when the resolved key changes.
    # This lets a fresh `tessera-mcp login` take effect on the next call with no restart.
    state: dict[str, object] = {"client": None, "key": None}

    def client() -> AsyncTessera | None:
        key = config.api_key or load_api_key()
        if not key:
            return None
        if state["client"] is None or state["key"] != key:
            state["client"] = AsyncTessera(api_key=key, base_url=config.base_url)
            state["key"] = key
        return state["client"]  # type: ignore[return-value]

    @mcp.tool()
    async def memory_recall(query: str) -> str:
        """Recall composed memory context (conventions, decisions, episodes) for this repo/task."""
        c = client()
        if c is None:
            return NO_KEY_MESSAGE
        return await tools.recall(c, query=query, user_id=config.repo, session_id=config.session)

    @mcp.tool()
    async def memory_search(query: str) -> str:
        """Raw hybrid search over memory (cheap, no LLM). Returns scored hits."""
        c = client()
        if c is None:
            return NO_KEY_MESSAGE
        return await tools.search(c, query=query, user_id=config.repo, session_id=config.session)

    @mcp.tool()
    async def memory_save_lesson(trigger: str, steps: list[str], success: str) -> str:
        """Save a reusable lesson.

        trigger=the situation, steps=what to do, success=the good outcome.
        """
        c = client()
        if c is None:
            return NO_KEY_MESSAGE
        return await tools.save_lesson(
            c,
            trigger=trigger,
            steps=steps,
            success=success,
            user_id=config.repo,
            session_id=config.session,
        )

    @mcp.tool()
    async def memory_recall_lessons(situation: str) -> str:
        """Recall lessons relevant to a situation (call before/while working on it)."""
        c = client()
        if c is None:
            return NO_KEY_MESSAGE
        return await tools.recall_lessons(
            c, situation=situation, user_id=config.repo, session_id=config.session
        )

    @mcp.tool()
    async def memory_note(text: str) -> str:
        """Record a durable repo convention (e.g. 'main branch only; commit when green')."""
        c = client()
        if c is None:
            return NO_KEY_MESSAGE
        return await tools.note(c, text=text, user_id=config.repo, session_id=config.session)

    return mcp


def main() -> None:
    build_server().run()
