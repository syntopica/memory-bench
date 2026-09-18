from pathlib import Path

import pytest

from membench import harness_commit as harness_commit_module
from membench.harness_commit import harness_commit


def test_it_reports_this_repository_s_commit():
    result = harness_commit()
    assert len(result["commit"]) == 40
    assert set(result["commit"]) <= set("0123456789abcdef")
    assert isinstance(result["dirty"], bool)


def test_it_admits_ignorance_outside_a_repository(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(harness_commit_module, "_REPOSITORY_ROOT", tmp_path)
    result = harness_commit()
    assert result == {"commit": "unknown", "dirty": True}


def test_a_git_binary_that_exists_but_cannot_run_is_the_unknown_case(
    monkeypatch: pytest.MonkeyPatch,
):
    def _unusable(*args: object, **kwargs: object) -> None:
        raise PermissionError("git is on PATH but is not executable")

    monkeypatch.setattr(harness_commit_module.subprocess, "run", _unusable)
    result = harness_commit()
    assert result == {"commit": "unknown", "dirty": True}
