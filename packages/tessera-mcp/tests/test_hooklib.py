import importlib.util
import json
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[3] / "integrations" / "claude-code" / "hooks"
_HOOKLIB = _HOOKS_DIR / "_hooklib.py"
_spec = importlib.util.spec_from_file_location("_hooklib", _HOOKLIB)
hooklib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hooklib)
# session_end imports `_hooklib` by name, so register it before loading that module.
sys.modules.setdefault("_hooklib", hooklib)

_SESSION_END = _HOOKS_DIR / "session_end.py"
_se_spec = importlib.util.spec_from_file_location("session_end", _SESSION_END)
session_end = importlib.util.module_from_spec(_se_spec)
_se_spec.loader.exec_module(session_end)


def test_repo_id_from_cwd() -> None:
    assert hooklib.repo_id_from_cwd("/Users/x/Custom/Personal/ai-memory") == "repo:ai-memory"


def test_session_start_context_block() -> None:
    block = hooklib.session_start_context("Repo uses uv.")
    assert "Tessera memory" in block
    assert "Repo uses uv." in block


def test_session_start_context_empty_is_none() -> None:
    assert hooklib.session_start_context("") is None


def test_load_transcript_flattens_nested_and_list_content(tmp_path: Path) -> None:
    # A real Claude Code transcript: turn text lives under rec["message"]["content"],
    # the top-level "content" is None, and assistant content is a list of blocks.
    records = [
        {
            "type": "user",
            "content": None,
            "message": {"role": "user", "content": "how do we install deps?"},
        },
        {
            "type": "assistant",
            "content": None,
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "ignore me"},
                    {"type": "text", "text": "Use uv, not pip."},
                    {"type": "tool_use", "name": "Bash", "input": {"command": "uv sync"}},
                ],
            },
        },
    ]
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    messages = session_end._load_transcript(str(p))

    assert messages == [
        {"role": "user", "content": "how do we install deps?"},
        {"role": "assistant", "content": "Use uv, not pip."},
    ]


def test_load_transcript_redacts_secrets(tmp_path: Path) -> None:
    records = [
        {
            "type": "user",
            "content": None,
            "message": {"role": "user", "content": "export OPENAI_API_KEY=sk-abcdef1234567890"},
        },
    ]
    p = tmp_path / "transcript.jsonl"
    p.write_text(json.dumps(records[0]) + "\n")

    messages = session_end._load_transcript(str(p))

    assert len(messages) == 1
    assert "sk-abcdef1234567890" not in messages[0]["content"]
    assert "REDACTED" in messages[0]["content"]
