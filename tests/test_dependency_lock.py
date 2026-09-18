from pathlib import Path

from membench import dependency_lock as dependency_lock_module
from membench.dependency_lock import dependency_lock


def test_it_hashes_the_lock_file_in_this_checkout():
    result = dependency_lock()
    assert result["path"] == "uv.lock"
    assert len(result["sha256"]) == 64


def test_it_admits_the_lock_is_absent(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(dependency_lock_module, "_REPOSITORY_ROOT", tmp_path)
    result = dependency_lock()
    assert result == {"path": "uv.lock", "sha256": "unknown"}
