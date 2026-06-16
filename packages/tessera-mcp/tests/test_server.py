import pytest
from tessera_mcp.config import Config
from tessera_mcp.server import build_server


async def test_build_server_registers_all_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = Config(repo="repo:demo", api_key="tsk_x", base_url="https://api.example.test")
    server = build_server(cfg)
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert names == {
        "memory_recall",
        "memory_search",
        "memory_save_lesson",
        "memory_recall_lessons",
        "memory_note",
    }
