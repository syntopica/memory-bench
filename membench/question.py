"""One labelled question of an evaluation set."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Question:
    """A question and the conversation a human confirmed answers it.

    Attributes:
        question_id: Stable identity, used in the raw results.
        question: The question text, as a person would ask it.
        answer_conversation_id: The labelled answer conversation, or `None`
            when the corpus deliberately cannot answer this question. That is
            a different fact from a missing label: a missing label is a
            corpus defect that `load_questions` refuses to load, while `None`
            here is the labeller's own verdict, recorded so a system that
            surfaces nothing for an unanswerable question is scored correctly
            rather than penalized for a miss it could not have avoided.
        as_of: The instant the question is asked as of, for a question whose
            correct answer depends on when it is asked - "what did we believe
            in March" is checkable only against a fixed date. `None` for a
            question with no such dependency. Track R asks only which
            conversation was found, so this is recorded for the corpus and
            never scored; do not route it into the scoring path.
        strata: Tags such as "es", "conversation", "no-overlap", "recent",
            "temporal-contradiction", used for descriptive breakdowns only.
    """

    question_id: str
    question: str
    answer_conversation_id: str | None
    strata: tuple[str, ...]
    as_of: str | None = None
