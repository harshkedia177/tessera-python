import pytest
from tessera_mcp.config import Config
from tessera_mcp.server import NO_KEY_MESSAGE, build_server

_TOOL_NAMES = {
    "memory_recall",
    "memory_search",
    "memory_save_lesson",
    "memory_recall_lessons",
    "memory_note",
}


async def test_build_server_registers_all_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = Config(repo="repo:demo", api_key="tsk_x", base_url="https://api.example.test")
    server = build_server(cfg)
    tools = await server.list_tools()
    assert {t.name for t in tools} == _TOOL_NAMES


async def test_tools_registered_even_without_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    # The server must still build and expose its tools with no key, so the MCP handshake
    # succeeds and the agent can be told (via the tool reply) how to configure one.
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    cfg = Config(repo="repo:demo", api_key=None)
    server = build_server(cfg)
    tools = await server.list_tools()
    assert {t.name for t in tools} == _TOOL_NAMES


async def test_tool_call_without_key_returns_guidance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    cfg = Config(repo="repo:demo", api_key=None)
    server = build_server(cfg)
    result = await server.call_tool("memory_recall", {"query": "anything"})
    # call_tool returns (content_blocks, ...) across mcp versions; find the text payload.
    blocks = result[0] if isinstance(result, tuple) else result
    text = " ".join(getattr(b, "text", "") for b in blocks)
    assert "login" in text
    assert NO_KEY_MESSAGE.split("\n")[0] in text
