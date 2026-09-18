"""Whether every labelled answer conversation appears in the top k."""

from collections.abc import Sequence


def recall_all_at_k(
    ranked: Sequence[str | None], answer_ids: Sequence[str], k: int
) -> float | None:
    """Return 1.0 when every labelled conversation is within the first k, None when k is too shallow.

    The strict half of the pair `recall_any_at_k` opens. A multi-hop question
    is answered by several conversations at once, and a system that surfaced
    one of three has not answered it; reporting only the permissive number
    would let that read as a hit. Reporting only this one would read a real
    partial success as total failure. Both are published, side by side, and
    are never averaged into a single "recall".

    Three labelled conversations cannot fit in one slot, so at a depth
    narrower than the label set this metric has observed nothing: not whether
    every label was found, and not whether the system tried. Scoring 0.0 there
    would publish a miss no system could avoid - a perfect system returning
    all three in rank order and a lazy one returning only the first score
    identically - and the mean of those zeros is the share of single-label
    questions in the question set, which describes the corpus and is not
    comparable across corpora. At `--k 1` that is the only all-recall
    published at all. So the number is None: undefined, exactly as it already
    is when a depth exceeds the `k` the run observed.

    The two boundaries look alike and are not the same thing, which is why one
    raises and one returns None. An empty label set is a malformed call - the
    question has no answer, and no depth will ever make this metric meaningful
    for it, so the caller is wrong to have asked. A depth narrower than the
    labels is a well-formed question asked at a depth that cannot answer it;
    the same question at depth 5 is scored normally.

    Args:
        ranked: Conversation ids in rank order, deduplicated. A None entry is
            a slot an unsourced hit spent; it never matches.
        answer_ids: Every labelled answer conversation. Must not be empty.
            Distinct conversations are what the depth is measured against, so
            a label repeated in the record needs no extra slot.
        k: How deep into the ranking to look.

    Returns:
        1.0 when all labelled conversations sit within k, 0.0 when at least
        one of them does not, and None when k is narrower than the number of
        distinct labels and therefore observed neither.

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
    wanted = set(answer_ids)
    if k < len(wanted):
        return None
    within = set(ranked[:k])
    return 1.0 if wanted <= within else 0.0
