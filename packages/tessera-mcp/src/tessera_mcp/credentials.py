"""Persistent API-key store, so the key lives in a file instead of the shell.

This is what makes setup one-step: the committed ``.mcp.json`` carries no secret, and the
server and hooks read the key from ``~/.tessera/credentials.json`` (written once by
``tessera-mcp login``). ``TESSERA_API_KEY`` in the environment still wins, for CI and
power users.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_ENV_KEY = "TESSERA_API_KEY"
_ENV_DIR = "TESSERA_CONFIG_DIR"


def config_dir() -> Path:
    """Directory holding Tessera's config (``~/.tessera`` unless overridden)."""
    override = os.environ.get(_ENV_DIR)
    return Path(override) if override else Path.home() / ".tessera"


def credentials_path() -> Path:
    """Path to the credentials file."""
    return config_dir() / "credentials.json"


def load_api_key() -> str | None:
    """Resolve the API key: ``TESSERA_API_KEY`` env first, then the credentials file."""
    env = os.environ.get(_ENV_KEY)
    if env:
        return env
    try:
        data = json.loads(credentials_path().read_text())
    except (OSError, ValueError):
        return None
    key = data.get("api_key") if isinstance(data, dict) else None
    return key if isinstance(key, str) and key else None


def has_api_key() -> bool:
    """True if an API key is resolvable from the env or the credentials file."""
    return load_api_key() is not None


def save_api_key(api_key: str) -> Path:
    """Write the API key to the credentials file (0600) and return its path."""
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"api_key": api_key}, indent=2) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        # Best effort: some filesystems (e.g. Windows) don't honor POSIX modes.
        pass
    return path


def describe_source() -> str:
    """Human-readable hint for ``status``: where the resolved key comes from."""
    if os.environ.get(_ENV_KEY):
        return f"{_ENV_KEY} environment variable"
    if credentials_path().exists():
        return str(credentials_path())
    return "not configured"
