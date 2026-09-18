"""Whether any labelled answer conversation appears in the top k."""

from collections.abc import Sequence


def recall_any_at_k(ranked: Sequence[str | None], answer_ids: Sequence[str], k: int) -> float:
    """Return 1.0 when at least one labelled conversation is within the first k.

    A question may be answered by more than one conversation - LongMemEval
    labels `answer_session_ids`, plural, and its multi-session questions are
    exactly the multi-hop ones. This is the permissive half of the pair: it
    asks whether the system found a way in. `recall_all_at_k` asks whether it
    found the whole answer, and the two are reported separately and never
    merged, because averaging them would describe neither. For a question with
    one label the two coincide by construction, which is why widening the
    label moved no existing number.

    Args:
        ranked: Conversation ids in rank order, deduplicated. A None entry is
            a slot an unsourced hit spent; it never matches.
        answer_ids: Every labelled answer conversation. Must not be empty.
        k: How deep into the ranking to look.

    Returns:
        1.0 when a labelled conversation sits within k, 0.0 otherwise.

    Raises:
        ValueError: If k is not positive, or `answer_ids` is empty. An empty
            label set is an unanswerable question, and there is no defensible
            number for it here: 0.0 publishes a miss the system could not have
            avoided, and 1.0 hands a hit to anything at all. The caller decides
            that the row is undefined, in the open, rather than this function
            deciding it silently.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if not answer_ids:
        raise ValueError("answer_ids must not be empty")
    within = set(ranked[:k])
    return 1.0 if any(answer_id in within for answer_id in answer_ids) else 0.0
