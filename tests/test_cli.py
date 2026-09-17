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


def _run(out: Path, **overrides: str) -> int:
    args = {
        "--adapter": "baseline_fts5",
        "--corpus": str(FIXTURE / "corpus.jsonl"),
        "--questions": str(FIXTURE / "questions.jsonl"),
        "--out": str(out),
    }
    args.update(overrides)
    argv = ["run"]
    for flag, value in args.items():
        argv.extend([flag, value])
    return main(argv)


def test_a_zero_k_is_refused_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--k": "0"})
    assert exit_code == 2
    assert not out.exists()


def test_a_negative_k_is_refused_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--k": "-3"})
    assert exit_code == 2
    assert not out.exists()


def test_a_missing_corpus_is_refused_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--corpus": str(FIXTURE / "no-such-corpus.jsonl")})
    assert exit_code == 2
    assert not out.exists()


def test_a_missing_questions_file_is_refused_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--questions": str(FIXTURE / "no-such-questions.jsonl")})
    assert exit_code == 2
    assert not out.exists()


def test_a_second_run_into_the_same_directory_is_refused(tmp_path: Path):
    out = tmp_path / "run"
    assert _run(out) == 0
    (out / "unrelated.txt").write_text("keep me", encoding="utf-8")
    manifest_before = (out / "manifest.json").read_text(encoding="utf-8")

    exit_code = _run(out)

    assert exit_code == 2
    assert (out / "manifest.json").read_text(encoding="utf-8") == manifest_before
    assert (out / "unrelated.txt").read_text(encoding="utf-8") == "keep me"


def test_force_permits_overwriting_a_previous_run(tmp_path: Path):
    out = tmp_path / "run"
    assert _run(out) == 0
    (out / "unrelated.txt").write_text("keep me", encoding="utf-8")

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
            "--force",
        ]
    )

    assert exit_code == 0
    assert (out / "unrelated.txt").read_text(encoding="utf-8") == "keep me"


def test_a_shallow_k_publishes_no_number_under_a_deeper_name(tmp_path: Path):
    out = tmp_path / "run"
    assert _run(out, **{"--k": "2"}) == 0
    rows = [json.loads(line) for line in (out / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(row["depth"] == 2 for row in rows)
    assert all(row["recall_at_5"] is None for row in rows)
    assert all(row["recall_at_10"] is None for row in rows)
    assert all(isinstance(row["recall_at_1"], float) for row in rows)
