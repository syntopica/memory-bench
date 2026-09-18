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
            {
                "question_id": "q1",
                "question": "x",
                "answer_conversation_id": "",
                "strata": ["en", "conversation", "overlap", "old"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="question q1 has no answer_conversation_id"):
        load_questions(path)


def test_an_explicit_null_answer_is_an_unanswerable_question(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(
        '{"question_id": "q1", "question": "que decidimos sobre el cache",'
        ' "answer_conversation_id": null, "strata": ["es", "conversation",'
        ' "no-overlap", "recent"]}\n',
        encoding="utf-8",
    )
    question = load_questions(path)[0]
    assert question.answer_conversation_id is None


def test_a_missing_answer_key_is_still_an_unlabelled_question(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(
        '{"question_id": "q1", "question": "x", "strata": ["en"]}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="answer_conversation_id"):
        load_questions(path)


def test_an_empty_string_answer_is_an_unlabelled_question(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(
        '{"question_id": "q1", "question": "x", "answer_conversation_id": "", "strata": ["en"]}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="answer_conversation_id"):
        load_questions(path)


def test_as_of_is_read_when_present_and_none_otherwise(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(
        '{"question_id": "q1", "question": "que creiamos en marzo",'
        ' "answer_conversation_id": "c4", "as_of": "2026-03-31T23:59:59Z",'
        ' "strata": ["es", "conversation", "overlap", "old",'
        ' "temporal-contradiction"]}\n'
        '{"question_id": "q2", "question": "x", "answer_conversation_id": "c1",'
        ' "strata": ["en", "conversation", "overlap", "old"]}\n',
        encoding="utf-8",
    )
    first, second = load_questions(path)
    assert first.as_of == "2026-03-31T23:59:59Z"
    assert second.as_of is None


def test_a_stratum_tag_outside_the_vocabulary_is_rejected(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(
        '{"question_id": "q1", "question": "x", "answer_conversation_id": "c1",'
        ' "strata": ["es", "conversation", "overlap", "reciente"]}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="reciente"):
        load_questions(path)
