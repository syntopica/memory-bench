"""Whether Track R can score a system's answer to one question at all."""

from collections.abc import Sequence

from membench.evidence import Evidence


def scoring_applicability(evidence: Sequence[Evidence], sources: Sequence[str | None]) -> str:
    """Return `"scored"`, or `"not_applicable"` when there is no provenance to score.

    Three states have to stay apart in the artifact. A system that returned
    nothing searched and failed: that is a miss, and it is scored. A system
    that returned evidence carrying conversation ids is scored on them, even
    when some of those hits are unsourced None slots. A system that returned
    evidence with no source conversation at all has no provenance to be right
    or wrong about; the spec says such a system "scores nothing here, and that
    is not a defect of the system", so it is excluded rather than recorded as
    a zero it did not earn.

    Args:
        evidence: The adapter's hits for this question, in rank order.
        sources: One entry per slot those hits spent, already cut at k; None
            marks a slot an unsourced hit spent.

    Returns:
        `"scored"` or `"not_applicable"`.
    """
    if evidence and all(source is None for source in sources):
        return "not_applicable"
    return "scored"
