"""What the CLI prints beside a mean taken over a different population."""

import json
from pathlib import Path

import pytest

from membench.cli import main


def _question(question_id: str, labels: list[str]) -> str:
    return json.dumps(
        {
            "question_id": question_id,
            "question": "indice de conversaciones en SQLite con FTS5",
            "answer_conversation_ids": labels,
            "strata": ["es", "conversation", "overlap", "old"],
        }
    )


@pytest.fixture
def _mixed_questions(tmp_path: Path) -> Path:
    path = tmp_path / "questions.jsonl"
    path.write_text(
        "\n".join(
            [
                _question("wide", ["c1", "c2", "c3"]),
                _question("narrow", ["c1"]),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_two_means_over_different_populations_print_different_denominators(
    tmp_path: Path, _mixed_questions: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The misreading this line exists to prevent, shown on a real run.

    A three-label question observes no `recall_all_at_1` - one slot cannot
    hold three conversations - while its `recall_any_at_1` is a real number.
    Printed without their counts the two means look comparable, and a reader
    would take an all-recall resting on one question for one resting on both.
    """
    fixture = Path(__file__).resolve().parent.parent / "corpora" / "fixture"
    code = main(
        [
            "run",
            "--adapter",
            "baseline_fts5",
            "--corpus",
            str(fixture / "corpus.jsonl"),
            "--questions",
            str(_mixed_questions),
            "--out",
            str(tmp_path / "run"),
        ]
    )
    assert code == 0
    printed = capsys.readouterr().out

    assert "recall_any_at_1@k=10: 1.0000 (over 2 questions)" in printed
    # Singular, like the abstention line beside it: this is published output.
    assert "recall_all_at_1@k=10: 1.0000 (over 1 question)" in printed
