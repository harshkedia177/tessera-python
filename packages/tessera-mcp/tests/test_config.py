from pathlib import Path

import pytest
from tessera_mcp.config import Config


def test_repo_env_overrides_autodetect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESSERA_REPO", "repo:explicit")
    monkeypatch.setenv("TESSERA_API_KEY", "tsk_x")
    monkeypatch.setenv("TESSERA_BASE_URL", "https://api.example.test")
    monkeypatch.setenv("TESSERA_SESSION", "task-7")
    cfg = Config.from_env()
    assert cfg.repo == "repo:explicit"
    assert cfg.api_key == "tsk_x"
    assert cfg.base_url == "https://api.example.test"
    assert cfg.session == "task-7"


def test_repo_autodetects_when_env_absent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # No TESSERA_REPO and a non-git dir -> falls back to the folder basename.
    monkeypatch.delenv("TESSERA_REPO", raising=False)
    target = tmp_path / "my-service"
    target.mkdir()
    cfg = Config.from_env(cwd=str(target))
    assert cfg.repo == "repo:my-service"


def test_api_key_loaded_from_store_when_env_absent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    (tmp_path / "credentials.json").write_text('{"api_key": "tsk_from_file"}')
    cfg = Config.from_env(cwd=str(tmp_path))
    assert cfg.api_key == "tsk_from_file"


def test_no_key_anywhere_is_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    cfg = Config.from_env(cwd=str(tmp_path))
    assert cfg.api_key is None
