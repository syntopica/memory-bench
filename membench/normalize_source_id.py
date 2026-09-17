"""Map a system's source identifier onto the corpus conversation id."""

_SYNTHESIS_NAMESPACE = "synthesis/"


def normalize_source_id(raw: str) -> str:
    """Return the corpus conversation id a source identifier refers to.

    Atrium writes synthesis records under a `synthesis/<conversation id>`
    namespace, so a synthesis hit and a raw hit on the same conversation must
    collapse to one answer before ranking.

    Args:
        raw: The source identifier the adapter reported.

    Returns:
        The conversation id, with a single leading synthesis namespace removed.
    """
    if raw.startswith(_SYNTHESIS_NAMESPACE):
        return raw[len(_SYNTHESIS_NAMESPACE) :]
    return raw
