"""One labelled question of an evaluation set."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Question:
    """A question and the conversations a human confirmed answer it.

    Attributes:
        question_id: Stable identity, used in the raw results.
        question: The question text, as a person would ask it.
        answer_conversation_ids: Every conversation a labeller confirmed
            answers this question, and empty when the corpus deliberately
            cannot answer it. The label is a set because real corpora label
            one - LongMemEval labels `answer_session_ids`, plural, and its
            multi-session questions are precisely the multi-hop ones, so a
            single label would mean dropping the hard questions and reporting
            a number that is not what it claims.

            The empty tuple is the only representation of "no answer", which
            is why it replaced a nullable single id: with two representations
            there were two things to guard, and the `None` label could
            false-match the `None` that marks an unsourced rank slot. There is
            nothing here for that hazard to reach any more.

            An empty set is a verdict, not a gap: a missing or blank label is a
            corpus defect that `load_questions` refuses to load, because it
            would score as a miss for every system regardless of what each one
            actually did.
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
    answer_conversation_ids: tuple[str, ...]
    strata: tuple[str, ...]
    as_of: str | None = None
