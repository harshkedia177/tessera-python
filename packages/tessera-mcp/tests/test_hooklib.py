import json
from pathlib import Path

from tessera_mcp import hooks


def test_session_start_context_block() -> None:
    block = hooks.session_start_context("Repo uses uv.")
    assert block is not None
    assert "Tessera memory" in block
    assert "Repo uses uv." in block


def test_session_start_context_empty_is_none() -> None:
    assert hooks.session_start_context("") is None


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

    messages = hooks._load_transcript(str(p))

    assert messages == [
        {"role": "user", "content": "how do we install deps?"},
        {"role": "assistant", "content": "Use uv, not pip."},
    ]


def test_load_transcript_redacts_secrets(tmp_path: Path) -> None:
    record = {
        "type": "user",
        "content": None,
        "message": {"role": "user", "content": "export OPENAI_API_KEY=sk-abcdef1234567890"},
    }
    p = tmp_path / "transcript.jsonl"
    p.write_text(json.dumps(record) + "\n")

    messages = hooks._load_transcript(str(p))

    assert len(messages) == 1
    assert "sk-abcdef1234567890" not in messages[0]["content"]
    assert "REDACTED" in messages[0]["content"]


def test_unknown_event_is_noop() -> None:
    assert hooks.run("nope") == 0
