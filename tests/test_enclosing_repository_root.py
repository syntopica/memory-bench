from pathlib import Path

from membench.enclosing_repository_root import enclosing_repository_root


def test_the_nearest_directory_holding_git_is_the_root(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "inner"
    (nested / ".git").mkdir(parents=True)
    assert enclosing_repository_root(nested / "a" / "file.jsonl") == nested


def test_a_git_file_marks_a_worktree_root(tmp_path: Path):
    (tmp_path / ".git").write_text("gitdir: /elsewhere\n")
    assert enclosing_repository_root(tmp_path / "file.jsonl") == tmp_path


def test_no_repository_above_the_file_is_none(tmp_path: Path):
    assert enclosing_repository_root(tmp_path / "file.jsonl") is None
