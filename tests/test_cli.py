import json
from pathlib import Path

from membench.cli import main

FIXTURE = Path(__file__).resolve().parent.parent / "corpora" / "fixture"


def test_a_baseline_run_over_the_fixture_produces_scores(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = main(
        [
            "run",
            "--adapter",
            "baseline_fts5",
            "--corpus",
            str(FIXTURE / "corpus.jsonl"),
            "--questions",
            str(FIXTURE / "questions.jsonl"),
            "--out",
            str(out),
        ]
    )
    assert exit_code == 0
    lines = (out / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6
    recalls = [json.loads(line)["recall_at_10"] for line in lines]
    assert sum(recalls) > 0


def test_an_unknown_adapter_is_refused(tmp_path: Path):
    exit_code = main(
        [
            "run",
            "--adapter",
            "nope",
            "--corpus",
            str(FIXTURE / "corpus.jsonl"),
            "--questions",
            str(FIXTURE / "questions.jsonl"),
            "--out",
            str(tmp_path / "run"),
        ]
    )
    assert exit_code == 2
