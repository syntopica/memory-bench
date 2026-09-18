"""Reciprocal of the rank at which the best-ranked labelled conversation appears."""

from collections.abc import Sequence


def reciprocal_rank(ranked: Sequence[str | None], answer_ids: Sequence[str]) -> float:
    """Return 1/rank of the **best-ranked** labelled conversation, or 0.0 when absent.

    With several labelled conversations there is a choice to make and it is
    published rather than left to the code: this measures the best-ranked one,
    so the metric answers "how quickly did the system reach the answer". The
    worst-ranked one is a different measurement - "how far must a reader go to
    have the whole answer" - and both are defensible. Choosing silently would
    change every published number without a version saying it changed, which
    is why the rule is stated here, in `README.md` and in the schema version's
    changelog. If the other measurement is ever wanted it is a new metric with
    its own name, not a redefinition of this one.

    For a question with one label this is the same function it always was.

    Args:
        ranked: Conversation ids in rank order, deduplicated. A None entry is
            a slot an unsourced hit spent; it never matches.
        answer_ids: Every labelled answer conversation. Must not be empty.

    Returns:
        The reciprocal of the 1-based rank of the first labelled conversation
        found, or 0.0 when none of them is in the ranking.

    Raises:
        ValueError: If `answer_ids` is empty. An unanswerable question has no
            target to be early or late about, so this is undefined rather than
            0.0; scoring it 0.0 would record a miss that could not have been
            avoided, and the caller must decide that in the open.
    """
    if not answer_ids:
        raise ValueError("answer_ids must not be empty")
    labelled = set(answer_ids)
    for position, source_id in enumerate(ranked, start=1):
        if source_id in labelled:
            return 1.0 / position
    return 0.0
