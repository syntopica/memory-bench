"""Recall at a fixed depth, or nothing when the run never looked that deep."""

from collections.abc import Callable, Sequence

Recall = Callable[[Sequence[str | None], Sequence[str], int], float | None]
"""A recall function: a ranking, the labelled conversations, and a depth.

It may itself return None for a depth it cannot observe - `recall_all_at_k`
does, for a depth narrower than the label set - and that None passes through
here unchanged: both absences mean the same thing to a reader, a metric the
run did not observe rather than a miss.
"""


def recall_at_depth(
    recall: Recall, ranked: Sequence[str | None], answer_ids: Sequence[str], depth: int, k: int
) -> float | None:
    """Return `recall` at `depth`, or None when `depth` is deeper than the run's `k`.

    A system asked for `k` hits was never given the chance to rank anything at
    position `k + 1`, so a miss there is unobserved, not a miss. Scoring it 0.0
    would publish a number under the name of a depth the run never reached.

    The rule is the same whichever recall is being measured, so it lives once
    and takes the recall as an argument: `recall_any_at_k` and
    `recall_all_at_k` are both guarded by this one statement of it, and a
    future third recall inherits it rather than restating it slightly
    differently.

    Args:
        recall: The recall to measure - `recall_any_at_k` or `recall_all_at_k`.
        ranked: Conversation ids in rank order, deduplicated, already cut at k.
            A None entry is a slot an unsourced hit spent; it never matches.
        answer_ids: Every labelled answer conversation.
        depth: The depth this metric is named for.
        k: The depth the run actually requested and observed.

    Returns:
        None when `depth` exceeds `k`, and otherwise whatever `recall` returns
        at that depth - which is itself None when the recall could not observe
        the depth it was given.

    Raises:
        ValueError: If k is not positive. `recall` raises on its own arguments.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if depth > k:
        return None
    return recall(ranked, answer_ids, depth)
