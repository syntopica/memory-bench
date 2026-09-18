from dataclasses import FrozenInstanceError

import pytest

from membench.question import Question


def test_as_of_defaults_to_none():
    question = Question(
        question_id="q1",
        question="por que se revirtio WAL",
        answer_conversation_id="c1",
        strata=("es", "conversation", "overlap", "recent"),
    )
    assert question.as_of is None


def test_question_is_frozen():
    question = Question(
        question_id="q1",
        question="x",
        answer_conversation_id="c1",
        strata=(),
    )
    with pytest.raises(FrozenInstanceError):
        question.question_id = "q2"
