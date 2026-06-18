"""Command-line entry point for ``tessera-mcp``.

tessera-mcp                  run the MCP server over stdio (default)
tessera-mcp serve            same as above
tessera-mcp login [KEY]      save your API key (prompts if KEY is omitted)
tessera-mcp status           show the resolved repo and whether a key is configured
tessera-mcp hook <event>     run a Claude Code hook (reads the event JSON on stdin)
"""

from __future__ import annotations

import argparse
import getpass
import sys


def _serve() -> int:
    from .server import build_server

    build_server().run()
    return 0


def _login(api_key: str | None) -> int:
    from .credentials import save_api_key

    key = (api_key or getpass.getpass("Tessera API key (tsk_live_...): ")).strip()
    if not key:
        sys.stderr.write("No key provided; nothing saved.\n")
        return 1
    path = save_api_key(key)
    print(f"Saved your Tessera API key to {path}.")
    print("Memory is ready. It is namespaced per git repo automatically — nothing else to set up.")
    return 0


def _status() -> int:
    from .config import Config
    from .credentials import describe_source

    cfg = Config.from_env()
    print(f"repo:    {cfg.repo}")
    if cfg.api_key:
        print(f"api_key: configured (source: {describe_source()})")
    else:
        print("api_key: NOT configured — run: tessera-mcp login")
    return 0


def _hook(event: str) -> int:
    from .hooks import run

    return run(event)


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)

    parser = argparse.ArgumentParser(
        prog="tessera-mcp",
        description="Tessera memory MCP server and setup helper.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="Run the MCP server over stdio (default).")
    p_login = sub.add_parser(
        "login", help="Save your Tessera API key to ~/.tessera/credentials.json."
    )
    p_login.add_argument("api_key", nargs="?", help="API key to save; prompts if omitted.")
    sub.add_parser("status", help="Show the resolved repo and whether a key is configured.")
    p_hook = sub.add_parser("hook", help="Run a Claude Code hook (reads the event JSON on stdin).")
    p_hook.add_argument(
        "event",
        choices=["session-start", "user-prompt-submit", "session-end"],
    )

    # No subcommand -> run the server (what MCP clients invoke as `... tessera-mcp`).
    if not args:
        raise SystemExit(_serve())

    ns = parser.parse_args(args)
    if ns.command in (None, "serve"):
        raise SystemExit(_serve())
    if ns.command == "login":
        raise SystemExit(_login(ns.api_key))
    if ns.command == "status":
        raise SystemExit(_status())
    if ns.command == "hook":
        raise SystemExit(_hook(ns.event))
    parser.print_help()
    raise SystemExit(2)
