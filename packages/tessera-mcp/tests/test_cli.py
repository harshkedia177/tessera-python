from pathlib import Path

import pytest
from tessera_mcp import cli, credentials


def test_login_saves_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    with pytest.raises(SystemExit) as exc:
        cli.main(["login", "tsk_live_abc"])
    assert exc.value.code == 0
    assert credentials.load_api_key() == "tsk_live_abc"


def test_login_prompts_when_key_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(cli.getpass, "getpass", lambda *a, **k: "tsk_live_prompted")
    with pytest.raises(SystemExit) as exc:
        cli.main(["login"])
    assert exc.value.code == 0
    assert credentials.load_api_key() == "tsk_live_prompted"


def test_login_empty_key_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(cli.getpass, "getpass", lambda *a, **k: "   ")
    with pytest.raises(SystemExit) as exc:
        cli.main(["login"])
    assert exc.value.code == 1


def test_status_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TESSERA_API_KEY", raising=False)
    monkeypatch.setenv("TESSERA_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TESSERA_REPO", "repo:demo")
    with pytest.raises(SystemExit) as exc:
        cli.main(["status"])
    assert exc.value.code == 0


def test_hook_unknown_event_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    # argparse rejects an event outside the allowed choices with exit code 2.
    with pytest.raises(SystemExit) as exc:
        cli.main(["hook", "bogus"])
    assert exc.value.code == 2
