"""Recall at a fixed depth, or nothing when the run never looked that deep."""

from collections.abc import Sequence

from membench.recall_at_k import recall_at_k


def recall_at_depth(
    ranked: Sequence[str], answer_id: str, depth: int, k: int
) -> float | None:
    """Return recall at `depth`, or None when `depth` is deeper than the run's `k`.

    A system asked for `k` hits was never given the chance to rank anything at
    position `k + 1`, so a miss there is unobserved, not a miss. Scoring it 0.0
    would publish a number under the name of a depth the run never reached.

    Args:
        ranked: Conversation ids in rank order, deduplicated, already cut at k.
        answer_id: The labelled answer conversation.
        depth: The depth this metric is named for.
        k: The depth the run actually requested and observed.

    Returns:
        1.0 or 0.0 while `depth` is within `k`, otherwise None.

    Raises:
        ValueError: If k is not positive.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if depth > k:
        return None
    return recall_at_k(ranked, answer_id, depth)
