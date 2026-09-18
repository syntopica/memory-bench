"""Whether every labelled answer conversation appears in the top k."""

from collections.abc import Sequence


def recall_all_at_k(ranked: Sequence[str | None], answer_ids: Sequence[str], k: int) -> float:
    """Return 1.0 when every labelled conversation is within the first k.

    The strict half of the pair `recall_any_at_k` opens. A multi-hop question
    is answered by several conversations at once, and a system that surfaced
    one of three has not answered it; reporting only the permissive number
    would let that read as a hit. Reporting only this one would read a real
    partial success as total failure. Both are published, side by side, and
    are never averaged into a single "recall".

    Args:
        ranked: Conversation ids in rank order, deduplicated. A None entry is
            a slot an unsourced hit spent; it never matches.
        answer_ids: Every labelled answer conversation. Must not be empty.
        k: How deep into the ranking to look.

    Returns:
        1.0 when all labelled conversations sit within k, 0.0 otherwise.

    Raises:
        ValueError: If k is not positive, or `answer_ids` is empty. The empty
            case is refused rather than answered because `all()` over nothing
            is True: an unanswerable question reaching this function would
            score a perfect 1.0 whatever came back, so a system that returned
            nothing at all would be rewarded for it. That is the free ride this
            guard exists to make unreachable even if a caller forgets to check
            `QuestionResult.answerable` first.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if not answer_ids:
        raise ValueError("answer_ids must not be empty")
    within = set(ranked[:k])
    return 1.0 if all(answer_id in within for answer_id in answer_ids) else 0.0
