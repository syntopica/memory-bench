"""Whether Track R can score a system's answer to one question at all."""

from collections.abc import Sequence

from membench.evidence import Evidence


def scoring_applicability(evidence: Sequence[Evidence], sources: Sequence[str]) -> str:
    """Return `"scored"`, or `"not_applicable"` when there is no provenance to score.

    Three states have to stay apart in the artifact. A system that returned
    nothing searched and failed: that is a miss, and it is scored. A system
    that returned evidence carrying conversation ids is scored on them. A
    system that returned evidence with no source conversation at all has no
    provenance to be right or wrong about; the spec says such a system "scores
    nothing here, and that is not a defect of the system", so it is excluded
    rather than recorded as a zero it did not earn.

    Args:
        evidence: The adapter's hits for this question, in rank order.
        sources: The conversation ids those hits resolved to, already cut at k.

    Returns:
        `"scored"` or `"not_applicable"`.
    """
    if evidence and not sources:
        return "not_applicable"
    return "scored"
