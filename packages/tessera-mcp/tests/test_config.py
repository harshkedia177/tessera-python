import pytest
from tessera_mcp.config import Config


def test_from_env_reads_repo_and_optionals(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESSERA_REPO", "repo:demo")
    monkeypatch.setenv("TESSERA_API_KEY", "tsk_x")
    monkeypatch.setenv("TESSERA_BASE_URL", "https://api.example.test")
    monkeypatch.setenv("TESSERA_SESSION", "task-7")
    cfg = Config.from_env()
    assert cfg.repo == "repo:demo"
    assert cfg.api_key == "tsk_x"
    assert cfg.base_url == "https://api.example.test"
    assert cfg.session == "task-7"


def test_from_env_requires_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TESSERA_REPO", raising=False)
    with pytest.raises(RuntimeError, match="TESSERA_REPO"):
        Config.from_env()
