"""Reduce ranked evidence to the ranked, deduplicated conversations behind it."""

from collections.abc import Sequence

from membench.evidence import Evidence
from membench.normalize_source_id import normalize_source_id


def ranked_sources(evidence: Sequence[Evidence]) -> tuple[str | None, ...]:
    """Return the ranking the evidence spends its retrieval budget on.

    One entry per slot, best first. A piece of evidence with no source
    conversation spends a slot and appears as None: the system returned
    something there, and it cannot be scored for source discovery. Sources
    inside one piece of evidence spend consecutive slots, so citing many
    conversations at once buys no extra depth. An identifier already seen
    keeps its better slot and is not emitted again; None is never
    deduplicated, because each unsourced hit spent its own slot.

    Args:
        evidence: The adapter's hits, already in rank order.

    Returns:
        One entry per slot in rank order: a conversation id, or None where
        the evidence carried no provenance.
    """
    slots: list[str | None] = []
    seen: set[str] = set()
    for piece in evidence:
        if not piece.source_ids:
            slots.append(None)
            continue
        for raw in piece.source_ids:
            source = normalize_source_id(raw)
            if source in seen:
                continue
            seen.add(source)
            slots.append(source)
    return tuple(slots)
