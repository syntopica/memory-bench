import argparse
from pathlib import Path

import pytest

from membench.adapters.baseline_fts5_adapter import BaselineFts5Adapter
from membench.build_adapter import ADAPTERS
from membench.cli import main
from membench.validate_run_paths import validate_run_paths

FIXTURE = Path(__file__).resolve().parent.parent / "corpora" / "fixture"


def _args(out: Path, *, force: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        k=10,
        corpus=FIXTURE / "corpus.jsonl",
        questions=FIXTURE / "questions.jsonl",
        out=out,
        force=force,
    )


def test_a_populated_workspace_without_a_manifest_is_refused(tmp_path: Path):
    workspace = tmp_path / "run" / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "index.db").write_bytes(b"left over")

    message = validate_run_paths(_args(tmp_path / "run"))

    assert message is not None
    assert "unfinished run" in message


def test_force_accepts_a_populated_workspace(tmp_path: Path):
    workspace = tmp_path / "run" / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "index.db").write_bytes(b"left over")

    assert validate_run_paths(_args(tmp_path / "run", force=True)) is None


def test_an_empty_workspace_is_not_a_leftover(tmp_path: Path):
    (tmp_path / "run" / "workspace").mkdir(parents=True)

    assert validate_run_paths(_args(tmp_path / "run")) is None


class _CrashingQueryAdapter(BaselineFts5Adapter):
    def query(self, question: str, k: int, token_budget: int | None):
        raise RuntimeError("the system crashed mid-run")


def test_the_run_after_a_crash_is_refused_until_forced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setitem(ADAPTERS, "crashing_query", _CrashingQueryAdapter)
    out = tmp_path / "run"
    argv = [
        "run",
        "--corpus",
        str(FIXTURE / "corpus.jsonl"),
        "--questions",
        str(FIXTURE / "questions.jsonl"),
        "--out",
        str(out),
    ]
    with pytest.raises(RuntimeError, match="crashed mid-run"):
        main([*argv, "--adapter", "crashing_query"])
    assert not (out / "manifest.json").exists()

    assert main([*argv, "--adapter", "baseline_fts5"]) == 2
    assert main([*argv, "--adapter", "baseline_fts5", "--force"]) == 0
