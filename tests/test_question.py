from dataclasses import FrozenInstanceError

import pytest

from membench.question import Question


def test_as_of_defaults_to_none():
    question = Question(
        question_id="q1",
        question="por que se revirtio WAL",
        answer_conversation_ids=("c1",),
        strata=("es", "conversation", "overlap", "recent"),
    )
    assert question.as_of is None


def test_an_unanswerable_question_carries_the_empty_label_set():
    question = Question(
        question_id="q1",
        question="algo que el corpus no responde",
        answer_conversation_ids=(),
        strata=(),
    )
    assert question.answer_conversation_ids == ()


def test_a_question_may_carry_several_labels():
    question = Question(
        question_id="q1",
        question="what did we decide across both threads",
        answer_conversation_ids=("c1", "c5"),
        strata=(),
    )
    assert question.answer_conversation_ids == ("c1", "c5")


def test_question_is_frozen():
    question = Question(
        question_id="q1",
        question="x",
        answer_conversation_ids=("c1",),
        strata=(),
    )
    with pytest.raises(FrozenInstanceError):
        question.question_id = "q2"
