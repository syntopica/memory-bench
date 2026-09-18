"""What the CLI prints on the abstention line when Track R cannot score the run."""

from pathlib import Path

import pytest

from membench.build_adapter import ADAPTERS
from membench.cli import main
from membench.evidence import Evidence
from membench.ingest_report import IngestReport

FIXTURE = Path(__file__).resolve().parent.parent / "corpora" / "fixture"


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


class _UnsourcedAdapter:
    """A stand-in whose answers never name a source conversation.

    It answers every answerable question with a memory it wrote itself and
    declines the unanswerable one, which is the shape that makes Track R
    inapplicable to the whole run while still earning a perfect abstention
    rate.
    """

    def __init__(self, workspace: Path) -> None:
        del workspace

    def setup(self) -> None:
        pass

    def ingest(self, corpus: object) -> IngestReport:
        del corpus
        return IngestReport(seconds=0.0, persisted_bytes=0, input_tokens=0, output_tokens=0)

    def query(self, question: str, k: int, token_budget: int | None) -> list:
        del k, token_budget
        if question.startswith("unanswerable"):
            return []
        return [
            Evidence(text="a memory I wrote myself", native_id="m1", source_ids=(), timestamp=None)
        ]

    def teardown(self) -> None:
        pass


def test_a_perfect_abstention_beside_no_scores_says_it_is_not_a_track_r_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    """The one number left standing must not read as a result.

    A system that answers every answerable question with unsourced text and
    declines the unanswerable one prints seven `n/a` metrics and a perfect
    abstention rate. No recall is lifted by that - abstention is never
    averaged into one - but a reader meeting `1.0000` alone on the page needs
    to be told, on that line, that it is independent of the applicability
    verdict and is not a Track R score.
    """
    monkeypatch.setitem(ADAPTERS, "unsourced", _UnsourcedAdapter)
    questions = tmp_path / "questions.jsonl"
    questions.write_text(
        '{"question_id": "u1", "question": "unanswerable one",'
        ' "answer_conversation_ids": [], "strata": ["en", "conversation",'
        ' "no-overlap", "recent"]}\n'
        '{"question_id": "a1", "question": "why did the deploy pipeline fail in February",'
        ' "answer_conversation_ids": ["c2"], "strata": ["en", "conversation",'
        ' "overlap", "old"]}\n',
        encoding="utf-8",
    )

    assert _run(tmp_path / "run", **{"--adapter": "unsourced", "--questions": str(questions)}) == 0

    printed = capsys.readouterr().out
    assert "recall_any_at_1@k=10: n/a" in printed
    assert "1 excluded as not applicable to Track R" in printed
    assert "abstention: 1.0000 over 1 unanswerable question" in printed
    assert "not a Track R score" in printed
