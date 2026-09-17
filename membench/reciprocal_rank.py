"""Reciprocal of the rank at which the labelled answer conversation appears."""

from collections.abc import Sequence


def reciprocal_rank(ranked: Sequence[str | None], answer_id: str) -> float:
    """Return 1/rank of the answer conversation, or 0.0 when it is absent.

    Args:
        ranked: Conversation ids in rank order, deduplicated. A None entry is
            a slot an unsourced hit spent; it never matches.
        answer_id: The labelled answer conversation.

    Returns:
        The reciprocal of the 1-based rank, or 0.0 when the answer is missing.
    """
    for position, source_id in enumerate(ranked, start=1):
        if source_id == answer_id:
            return 1.0 / position
    return 0.0
