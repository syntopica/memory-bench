"""One labelled question of an evaluation set."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Question:
    """A question and the conversation a human confirmed answers it.

    Attributes:
        question_id: Stable identity, used in the raw results.
        question: The question text, as a person would ask it.
        answer_conversation_id: The labelled answer conversation.
        strata: Tags such as "es", "conversation", "no-overlap", "recent",
            "temporal-contradiction", used for descriptive breakdowns only.
    """

    question_id: str
    question: str
    answer_conversation_id: str
    strata: tuple[str, ...]
