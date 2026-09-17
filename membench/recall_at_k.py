"""Whether the labelled answer conversation appears in the top k."""

from collections.abc import Sequence


def recall_at_k(ranked: Sequence[str], answer_id: str, k: int) -> float:
    """Return 1.0 when the answer conversation is within the first k, else 0.0.

    Each question has exactly one labelled relevant conversation, so recall
    here is a hit rate; it is named recall because that is what the literature
    this is compared against reports.

    Args:
        ranked: Conversation ids in rank order, deduplicated.
        answer_id: The labelled answer conversation.
        k: How deep into the ranking to look.

    Returns:
        1.0 on a hit within k, 0.0 otherwise.

    Raises:
        ValueError: If k is not positive.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    return 1.0 if answer_id in ranked[:k] else 0.0
