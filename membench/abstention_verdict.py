"""Whether a system abstained on a question it was not meant to be able to answer."""

from collections.abc import Sequence


def abstention_verdict(ranked: Sequence[str | None], *, answerable: bool) -> bool | None:
    """Return whether the system abstained, or None where the question does not arise.

    Abstaining means returning nothing at all. It is only a verdict worth
    recording on a question the corpus deliberately cannot answer: there,
    silence is the correct behaviour and is the one thing the unanswerable
    population measures. On an answerable question silence is simply a miss,
    already scored as one by every recall, so recording it again under a name
    that reads like a virtue would invite a reader to average the two.

    Returning evidence that names no source is **not** abstaining. The system
    answered; it answered without provenance. Counting it as abstention would
    reward a system for emitting unattributable text on exactly the questions
    it should have declined, which is the shape of the free rides this
    harness has closed before.

    Args:
        ranked: The full ranking of slots the system's evidence spent, before
            any depth cut. A None entry is a slot an unsourced hit spent, and
            its presence means the system returned something.
        answerable: Whether the corpus can answer this question at all.

    Returns:
        True when the system returned nothing, False when it returned
        something, and None on an answerable question.
    """
    if answerable:
        return None
    return not ranked
