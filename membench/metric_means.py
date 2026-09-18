"""Average a Track R run over the questions it could actually score."""

from collections.abc import Sequence

from membench.question_result import QuestionResult

_METRICS = ("recall_at_1", "recall_at_5", "recall_at_10", "reciprocal_rank")


def metric_means(results: Sequence[QuestionResult]) -> dict[str, float | None]:
    """Return one mean per metric, over the rows that observed it.

    A missing number is never averaged as a zero. Applicability is a property
    of the run, so the skip below is all-or-nothing: either every row is
    `"scored"` and averaged, or the system's evidence named no source on any
    question, it is not applicable to this track, and every metric is None. A
    partial exclusion cannot exist, so no row can be dropped from a
    denominator to lift a mean. A depth the run never reached still has no mean at all,
    rather than a mean of the misses it never made.

    Args:
        results: Every question's result, in question order.

    Returns:
        A mean per metric, None where no row observed that metric.
    """
    scored = [result for result in results if result.applicability == "scored"]
    means: dict[str, float | None] = {}
    for metric in _METRICS:
        observed = [value for result in scored if (value := getattr(result, metric)) is not None]
        means[metric] = sum(observed) / len(observed) if observed else None
    return means
