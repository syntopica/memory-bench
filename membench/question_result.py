"""What Track R measured for one question."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuestionResult:
    """One question's source-discovery result.

    Attributes:
        question_id: Which question this is.
        strata: The question's tags, for descriptive breakdowns only.
        ranked_sources: One entry per slot the system spent, best first. A
            None entry is a slot an unsourced hit spent: the system returned
            something there, and it carried no conversation to score.
        applicability: `"scored"`, or `"not_applicable"` when the system
            produced no source conversation anywhere in the whole run. It is a
            verdict on the run, so every row of a run carries the same value
            and every metric below is None on all of them: such a system is
            unscorable on this track. Within a scored run there is no
            exclusion - a response that carried no provenance scores the
            misses it earned, exactly as returning nothing does.
        depth: The `k` this run requested and observed. Every metric below is
            measured at that depth and means nothing without it.
        truncated: True when the system offered more slots than `k` and the
            ranking was cut, so a reader knows the absence of a later source
            is the harness's choice and not the system's.
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
    ranked_sources: tuple[str | None, ...]
    applicability: str
    depth: int
    truncated: bool
    recall_at_1: float | None
    recall_at_5: float | None
    recall_at_10: float | None
    reciprocal_rank: float | None
    seconds: float
    evidence_texts: tuple[str, ...]
