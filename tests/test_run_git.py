from pathlib import Path

import pytest

from membench import run_git as run_git_module
from membench.run_git import run_git


def test_a_failing_command_is_none(tmp_path: Path):
    assert run_git(["rev-parse", "HEAD"], tmp_path) is None


def test_git_that_cannot_start_is_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def _unusable(*args: object, **kwargs: object) -> None:
        raise PermissionError("git is on PATH but is not executable")

    monkeypatch.setattr(run_git_module.subprocess, "run", _unusable)
    assert run_git(["status"], tmp_path) is None
