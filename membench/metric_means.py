"""Average a Track R run over the questions it could actually score."""

from collections.abc import Sequence

from membench.question_result import QuestionResult

_METRICS = (
    "recall_any_at_1",
    "recall_any_at_5",
    "recall_any_at_10",
    "recall_all_at_1",
    "recall_all_at_5",
    "recall_all_at_10",
    "reciprocal_rank",
)


def metric_means(results: Sequence[QuestionResult]) -> dict[str, float | None]:
    """Return one mean per metric, over the rows that were answerable and scored.

    A missing number is never averaged as a zero. Applicability is a property
    of the run, so that skip is all-or-nothing: either every row is `"scored"`
    and averaged, or the system's evidence named no source on any question, it
    is not applicable to this track, and every metric is None. A partial
    exclusion cannot exist, so no row can be dropped from a denominator to lift
    a mean. A depth the run never reached still has no mean at all, rather than
    a mean of the misses it never made.

    Unanswerable rows are excluded too, and that exclusion is safe for a
    different reason: it is decided by the question, identically for every
    system measured on the set, so no system can move itself in or out of the
    denominator by changing what it returns. Merging the two populations is
    what would be the free ride. An unanswerable question has no conversation
    to find, so whatever is counted for it is counted for returning nothing:
    scored as a miss it would punish the correct behaviour, and scored as a hit
    it would hand a perfect recall to a system that answers every question with
    silence. Neither is a retrieval result. `abstention_rate` reports that
    population on its own, and the two numbers are never averaged together.

    The filter is stated here and not only upstream on purpose. `run_track_r`
    already leaves every metric None on an unanswerable row, so today the two
    agree; if that ever slipped, this function would quietly average a number
    that describes nothing, and the mean would move without any test noticing.

    `recall_any_*` and `recall_all_*` are likewise separate means and are not
    to be combined into one "recall": one asks whether the system found a way
    into a multi-hop question, the other whether it found the whole answer.

    Args:
        results: Every question's result, in question order.

    Returns:
        A mean per metric, None where no row observed that metric.
    """
    scored = [
        result for result in results if result.answerable and result.applicability == "scored"
    ]
    means: dict[str, float | None] = {}
    for metric in _METRICS:
        observed = [value for result in scored if (value := getattr(result, metric)) is not None]
        means[metric] = sum(observed) / len(observed) if observed else None
    return means
