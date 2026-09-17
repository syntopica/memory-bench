from pathlib import Path

from membench.load_corpus import load_corpus
from membench.load_questions import load_questions

FIXTURE = Path(__file__).resolve().parent.parent / "corpora" / "fixture"


def test_every_question_points_at_a_conversation_in_the_corpus():
    corpus_ids = {
        conversation.conversation_id for conversation in load_corpus(FIXTURE / "corpus.jsonl")
    }
    for question in load_questions(FIXTURE / "questions.jsonl"):
        assert question.answer_conversation_id in corpus_ids


def test_the_fixture_holds_a_reversal_pair():
    questions = load_questions(FIXTURE / "questions.jsonl")
    assert any("temporal-contradiction" in question.strata for question in questions)


def test_the_fixture_covers_both_languages():
    strata = {
        stratum
        for question in load_questions(FIXTURE / "questions.jsonl")
        for stratum in question.strata
    }
    assert {"es", "en"} <= strata
