"""What Track R measured for one question."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuestionResult:
    """One question's source-discovery result.

    Attributes:
        question_id: Which question this is.
        strata: The question's tags, for descriptive breakdowns only.
        ranked_sources: Conversation ids the system returned, best first.
        depth: The `k` this run requested and observed. Every metric below is
            measured at that depth and means nothing without it.
        recall_at_1: 1.0 when the answer conversation ranked first.
        recall_at_5: 1.0 when it appeared in the first five, None when the run
            never looked five deep.
        recall_at_10: 1.0 when it appeared in the first ten, None when the run
            never looked ten deep.
        reciprocal_rank: 1/rank of the answer conversation within `depth`, 0.0
            when it is absent from the observed ranking. This is RR at `depth`:
            a miss inside an observed depth is a real zero for that metric, and
            `depth` is recorded so it is never read as RR at full depth.
        seconds: Wall-clock duration of this single query.
        evidence_texts: The evidence as returned, kept so a miss can be read.
    """

    question_id: str
    strata: tuple[str, ...]
    ranked_sources: tuple[str, ...]
    depth: int
    recall_at_1: float | None
    recall_at_5: float | None
    recall_at_10: float | None
    reciprocal_rank: float
    seconds: float
    evidence_texts: tuple[str, ...]
