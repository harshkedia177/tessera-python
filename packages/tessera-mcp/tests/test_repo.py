import subprocess
from pathlib import Path

import pytest
from tessera_mcp import repo


@pytest.mark.parametrize(
    "url,expected",
    [
        ("git@github.com:owner/repo.git", "owner/repo"),
        ("https://github.com/owner/repo.git", "owner/repo"),
        ("https://github.com/owner/repo", "owner/repo"),
        ("ssh://git@gitlab.com/group/sub.git", "group/sub"),
        ("https://github.com/owner/repo/", "owner/repo"),
    ],
)
def test_slug_from_remote(url: str, expected: str) -> None:
    assert repo._slug_from_remote(url) == expected


def test_detect_falls_back_to_basename_without_git(tmp_path: Path) -> None:
    target = tmp_path / "lonely-dir"
    target.mkdir()
    assert repo.detect_repo_id(str(target)) == "repo:lonely-dir"


def _have_git() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


@pytest.mark.skipif(not _have_git(), reason="git not available")
def test_detect_uses_remote_when_present(tmp_path: Path) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(tmp_path), *args], capture_output=True, check=True)

    git("init", "-q")
    git("remote", "add", "origin", "git@github.com:acme/widgets.git")
    assert repo.detect_repo_id(str(tmp_path)) == "repo:acme/widgets"


@pytest.mark.skipif(not _have_git(), reason="git not available")
def test_detect_uses_toplevel_name_without_remote(tmp_path: Path) -> None:
    project = tmp_path / "no-remote-proj"
    project.mkdir()
    subprocess.run(["git", "-C", str(project), "init", "-q"], capture_output=True, check=True)
    assert repo.detect_repo_id(str(project)) == "repo:no-remote-proj"
