"""Whether Track R can score a system at all, decided once over the whole run."""

from collections.abc import Iterable, Sequence


def run_applicability(rankings: Iterable[Sequence[str | None]]) -> str:
    """Return `"scored"`, or `"not_applicable"` when the run has no provenance anywhere.

    Applicability is a property of the system, not of one response. The only
    carve-out the design record grants is architectural: a system whose
    memories have no unique source conversation "scores nothing here, and that
    is not a defect of the system". A system that cited a conversation once has
    that provenance, so every question it was asked is scored on it - including
    the questions it answered with nothing, and the questions it answered with
    text carrying no source. Those are misses it earned.

    The carve-out needs the architecture to have been exercised, so it takes
    evidence that carried no source, not an absence of evidence. A system that
    returned nothing anywhere searched and failed every time, which is what a
    zero records; excluding it would let "I find nothing" read as "this track
    does not apply to me", and that is the same free ride one level further
    out. A run of no questions at all observes neither, and has no rows to
    carry a verdict either way.

    Deciding this per question is the free ride this function exists to close.
    A system that stripped provenance from the questions it expected to lose
    had exactly those rows dropped from the denominator instead of scored zero,
    which was measured taking every headline metric from 0.5 to 1.0 on
    unchanged retrieval - and it punished honest abstention, which scored the
    zero the junk avoided. There is no mixed run: either every row is
    `"scored"` or every row is `"not_applicable"`, so a partial exclusion
    cannot exist and therefore cannot inflate a mean.

    Args:
        rankings: One entry per question, each the full ranking of slots that
            question's evidence spent before any depth cut; None marks a slot
            an unsourced hit spent. The full ranking is what must be passed:
            a real conversation cited past depth k is still provenance, and
            the system is scored the miss rather than excluded.

    Returns:
        `"scored"` or `"not_applicable"`, for every row in the run alike.
    """
    observed_evidence = False
    for ranking in rankings:
        if any(source is not None for source in ranking):
            return "scored"
        observed_evidence = observed_evidence or bool(ranking)
    return "not_applicable" if observed_evidence else "scored"
