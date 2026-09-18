"""How often a system correctly returned nothing, over the questions with no answer."""

from collections.abc import Sequence

from membench.question_result import QuestionResult


def abstention_rate(results: Sequence[QuestionResult]) -> float | None:
    """Return the share of unanswerable questions the system abstained on.

    This is the unanswerable population's one number, and it is reported
    beside the retrieval metrics and never inside them. The two populations
    answer different questions - "when there was something to find, was it
    found" and "when there was nothing to find, was that recognised" - and a
    single blended figure answers neither while hiding the trade between them.

    Merging them would also be a free ride, of the same family as the three
    this harness has already closed. A system that returns nothing on every
    question scores 0.0 on every recall and 1.0 here; averaged together those
    would report a mediocre system that never retrieved anything as an average
    one. Kept apart, the run says plainly that it found nothing and declined
    everything, which is what it did.

    Args:
        results: Every question's result, in question order. Applicability is
            deliberately not consulted: whether the system returned anything
            at all is observed even for a system Track R cannot score, and
            that observation is honest to report.

    Returns:
        The share of unanswerable rows that abstained, or None when the run
        held no unanswerable question - the rate was not observed, and 0.0
        would claim a system failed to decline questions it was never asked.
    """
    unanswerable = [result for result in results if not result.answerable]
    if not unanswerable:
        return None
    return sum(1.0 for result in unanswerable if result.abstained) / len(unanswerable)
