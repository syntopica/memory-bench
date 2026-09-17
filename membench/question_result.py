"""What Track R measured for one question."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuestionResult:
    """One question's source-discovery result.

    Attributes:
        question_id: Which question this is.
        strata: The question's tags, for descriptive breakdowns only.
        ranked_sources: Conversation ids the system returned, best first.
        recall_at_1: 1.0 when the answer conversation ranked first.
        recall_at_5: 1.0 when it appeared in the first five.
        recall_at_10: 1.0 when it appeared in the first ten.
        reciprocal_rank: 1/rank of the answer conversation, 0.0 when absent.
        seconds: Wall-clock duration of this single query.
        evidence_texts: The evidence as returned, kept so a miss can be read.
    """

    question_id: str
    strata: tuple[str, ...]
    ranked_sources: tuple[str, ...]
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    reciprocal_rank: float
    seconds: float
    evidence_texts: tuple[str, ...]
