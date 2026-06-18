"""Resolved configuration for the Tessera MCP server.

The repo identity is auto-detected from the working directory (see ``repo``); the API key
comes from the persistent store (see ``credentials``). Both can be overridden by the
environment, but neither has to be set for the plugin to install cleanly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .credentials import load_api_key
from .repo import detect_repo_id


@dataclass(frozen=True)
class Config:
    """Resolved server config: repo is the Tessera user_id, session the optional session_id."""

    repo: str
    api_key: str | None = None
    base_url: str | None = None
    session: str | None = None

    @classmethod
    def from_env(cls, cwd: str | None = None) -> Config:
        # TESSERA_REPO overrides the auto-detected identity; otherwise isolate per repo.
        repo = os.environ.get("TESSERA_REPO") or detect_repo_id(cwd)
        return cls(
            repo=repo,
            api_key=load_api_key(),
            base_url=os.environ.get("TESSERA_BASE_URL"),
            session=os.environ.get("TESSERA_SESSION"),
        )
