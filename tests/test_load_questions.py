import json
from pathlib import Path

import pytest

from membench.load_questions import load_questions


def test_loads_a_labelled_question(tmp_path: Path):
    path = tmp_path / "questions.jsonl"
    path.write_text(
        json.dumps(
            {
                "question_id": "q1",
                "question": "por que se revirtio WAL",
                "answer_conversation_id": "c1",
                "strata": ["es", "conversation", "overlap", "recent"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    questions = load_questions(path)
    assert questions[0].question_id == "q1"
    assert questions[0].answer_conversation_id == "c1"
    assert questions[0].strata == ("es", "conversation", "overlap", "recent")


def test_an_unlabelled_question_is_rejected(tmp_path: Path):
    path = tmp_path / "questions.jsonl"
    path.write_text(
        json.dumps(
            {"question_id": "q1", "question": "x", "answer_conversation_id": "", "strata": []}
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="question q1 has no answer_conversation_id"):
        load_questions(path)
