"""Average a Track R run over the questions it could actually score."""

from collections.abc import Sequence

from membench.question_result import QuestionResult

_METRICS = ("recall_at_1", "recall_at_5", "recall_at_10", "reciprocal_rank")


def track_r_means(results: Sequence[QuestionResult]) -> dict[str, float | None]:
    """Return one mean per metric, over the rows that observed it.

    A missing number is never averaged as a zero. A system with no provenance
    is not applicable to this track and its rows are skipped entirely, and a
    depth the run never reached has no mean at all rather than a mean of the
    misses it never made.

    Args:
        results: Every question's result, in question order.

    Returns:
        A mean per metric, None where no row observed that metric.
    """
    scored = [result for result in results if result.applicability == "scored"]
    means: dict[str, float | None] = {}
    for metric in _METRICS:
        observed = [
            value for result in scored if (value := getattr(result, metric)) is not None
        ]
        means[metric] = sum(observed) / len(observed) if observed else None
    return means
