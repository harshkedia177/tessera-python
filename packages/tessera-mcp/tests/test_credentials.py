from pathlib import Path

import pytest
from tessera_mcp import credentials


def test_env_key_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TESSERA_API_KEY", "tsk_env")
    (tmp_path / "credentials.json").write_text('{"api_key": "tsk_file"}')
    assert credentials.load_api_key() == "tsk_env"


def test_falls_back_to_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    (tmp_path / "credentials.json").write_text('{"api_key": "tsk_file"}')
    assert credentials.load_api_key() == "tsk_file"
    assert credentials.has_api_key() is True


def test_missing_everywhere(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    assert credentials.load_api_key() is None
    assert credentials.has_api_key() is False


def test_save_then_load_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    path = credentials.save_api_key("tsk_saved")
    assert path == tmp_path / "credentials.json"
    assert credentials.load_api_key() == "tsk_saved"


def test_corrupt_file_is_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    (tmp_path / "credentials.json").write_text("not json{")
    assert credentials.load_api_key() is None
