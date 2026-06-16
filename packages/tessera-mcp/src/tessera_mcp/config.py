"""Environment-driven configuration for the Tessera MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Resolved server config: repo is the Tessera user_id, session the optional session_id."""

    repo: str
    api_key: str | None = None
    base_url: str | None = None
    session: str | None = None

    @classmethod
    def from_env(cls) -> Config:
        repo = os.environ.get("TESSERA_REPO")
        if not repo:
            raise RuntimeError(
                "TESSERA_REPO is required: the repo identity used as the Tessera user_id."
            )
        return cls(
            repo=repo,
            api_key=os.environ.get("TESSERA_API_KEY"),
            base_url=os.environ.get("TESSERA_BASE_URL"),
            session=os.environ.get("TESSERA_SESSION"),
        )
