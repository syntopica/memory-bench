from pathlib import Path

from membench.clear_workspace import clear_workspace


def test_it_removes_a_populated_workspace(tmp_path: Path):
    workspace = tmp_path / "workspace"
    (workspace / "nested").mkdir(parents=True)
    (workspace / "nested" / "state.bin").write_bytes(b"left over")

    clear_workspace(workspace)

    assert not workspace.exists()


def test_a_missing_workspace_is_not_an_error(tmp_path: Path):
    clear_workspace(tmp_path / "workspace")

    assert not (tmp_path / "workspace").exists()


def test_a_symlinked_workspace_is_unlinked_not_followed(tmp_path: Path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "keep.txt").write_text("not the harness's", encoding="utf-8")
    workspace = tmp_path / "workspace"
    workspace.symlink_to(elsewhere, target_is_directory=True)

    clear_workspace(workspace)

    assert not workspace.exists()
    assert (elsewhere / "keep.txt").read_text(encoding="utf-8") == "not the harness's"
