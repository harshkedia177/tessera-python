"""Automatic repo identity: the memory namespace, derived from where we are running.

The MCP server and the hooks both call ``detect_repo_id`` so memory is isolated per repo
with nothing for the user to declare. Order of preference:

1. git ``remote.origin.url`` -> ``owner/repo`` (stable across clones and folder renames),
2. the git toplevel folder name,
3. the working-directory basename.

``TESSERA_REPO`` in the environment overrides all of this (handled in ``config``).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

_SPLIT = re.compile(r"[/:]")


def _git(cwd: str, *args: str) -> str | None:
    """Run a read-only git command in ``cwd``; return trimmed stdout or None."""
    try:
        proc = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    return out or None


def _slug_from_remote(url: str) -> str | None:
    """Normalize a git remote URL to ``owner/repo``.

    Handles scp-style (``git@github.com:owner/repo.git``) and URL
    (``https://github.com/owner/repo.git``) forms.
    """
    cleaned = url.strip().removesuffix("/").removesuffix(".git")
    parts = [p for p in _SPLIT.split(cleaned) if p]
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    return None


def detect_repo_id(cwd: str | None = None) -> str:
    """Return the ``repo:<slug>`` identity used as the Tessera ``user_id``."""
    base = cwd or os.getcwd()
    remote = _git(base, "config", "--get", "remote.origin.url")
    slug = _slug_from_remote(remote) if remote else None
    if not slug:
        top = _git(base, "rev-parse", "--show-toplevel")
        slug = Path(top).name if top else None
    if not slug:
        slug = Path(base).name or "unknown"
    return f"repo:{slug}"
