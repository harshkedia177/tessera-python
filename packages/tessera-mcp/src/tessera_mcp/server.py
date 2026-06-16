"""FastMCP server exposing Tessera memory tools over stdio."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from tessera_memory import AsyncTessera

from . import tools
from .config import Config


def build_server(config: Config | None = None) -> FastMCP:
    config = config or Config.from_env()
    client = AsyncTessera(api_key=config.api_key, base_url=config.base_url)
    mcp = FastMCP("tessera_memory")

    @mcp.tool()
    async def memory_recall(query: str) -> str:
        """Recall composed memory context (conventions, decisions, episodes) for this repo/task."""
        return await tools.recall(
            client, query=query, user_id=config.repo, session_id=config.session
        )

    @mcp.tool()
    async def memory_search(query: str) -> str:
        """Raw hybrid search over memory (cheap, no LLM). Returns scored hits."""
        return await tools.search(
            client, query=query, user_id=config.repo, session_id=config.session
        )

    @mcp.tool()
    async def memory_save_lesson(trigger: str, steps: list[str], success: str) -> str:
        """Save a reusable lesson.

        trigger=the situation, steps=what to do, success=the good outcome.
        """
        return await tools.save_lesson(
            client,
            trigger=trigger,
            steps=steps,
            success=success,
            user_id=config.repo,
            session_id=config.session,
        )

    @mcp.tool()
    async def memory_recall_lessons(situation: str) -> str:
        """Recall lessons relevant to a situation (call before/while working on it)."""
        return await tools.recall_lessons(
            client, situation=situation, user_id=config.repo, session_id=config.session
        )

    @mcp.tool()
    async def memory_note(text: str) -> str:
        """Record a durable repo convention (e.g. 'main branch only; commit when green')."""
        return await tools.note(client, text=text, user_id=config.repo, session_id=config.session)

    return mcp


def main() -> None:
    build_server().run()
