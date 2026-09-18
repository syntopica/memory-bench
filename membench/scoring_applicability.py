"""Whether Track R can score a system's answer to one question at all."""

from collections.abc import Sequence

from membench.evidence import Evidence


def scoring_applicability(evidence: Sequence[Evidence], sources: Sequence[str | None]) -> str:
    """Return `"scored"`, or `"not_applicable"` when there is no provenance to score.

    Three states have to stay apart in the artifact. A system that returned
    nothing searched and failed: that is a miss, and it is scored. A system
    that returned evidence carrying conversation ids is scored on them, even
    when some of those hits are unsourced None slots, and even when the real
    id sits past the depth the run is scoring at: ranking it too low is a
    real miss, not an absence of provenance. A system that returned evidence
    with no source conversation at all, anywhere in the full ranking, has no
    provenance to be right or wrong about; the spec says such a system
    "scores nothing here, and that is not a defect of the system", so it is
    excluded rather than recorded as a zero it did not earn. This is why the
    caller must pass the full ranking here, not one already cut to a depth:
    applicability is a property of the system, not of the retrieval budget it
    was asked to work within.

    Args:
        evidence: The adapter's hits for this question, in rank order.
        sources: One entry per slot those hits spent, the full ranking before
            any depth cut; None marks a slot an unsourced hit spent.

    Returns:
        `"scored"` or `"not_applicable"`.
    """
    if evidence and all(source is None for source in sources):
        return "not_applicable"
    return "scored"
