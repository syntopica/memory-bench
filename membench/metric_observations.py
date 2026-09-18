"""How many questions each Track R mean was actually taken over."""

from collections.abc import Sequence

from membench.metric_means import METRICS
from membench.question_result import QuestionResult


def metric_observations(results: Sequence[QuestionResult]) -> dict[str, int]:
    """Return how many rows observed each metric.

    The means are not all taken over the same questions, and printing them in
    one block without their counts invites the reading that they are. A
    `recall_all_at_1` is undefined for every question carrying more than one
    distinct label, so on a set where most questions are multi-label its mean
    may rest on a handful of rows while `recall_any_at_1` beside it rests on
    all of them. Both numbers are honest; side by side and undenominated they
    are misleading, and a benchmark asking to be cited cannot publish a mean
    whose population is stated only in a docstring.

    This counts the same rows `metric_means` averages, by the same rule, so
    the two cannot drift: a metric's count is the length of the list its mean
    divided by.

    Args:
        results: Every question's result, in question order.

    Returns:
        One count per metric, 0 where no row observed it.
    """
    scored = [
        result for result in results if result.answerable and result.applicability == "scored"
    ]
    return {
        metric: sum(1 for result in scored if getattr(result, metric) is not None)
        for metric in METRICS
    }
