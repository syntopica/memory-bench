"""Reduce ranked evidence to the ranked, deduplicated conversations behind it."""

from collections.abc import Sequence

from membench.evidence import Evidence
from membench.normalize_source_id import normalize_source_id


def ranked_sources(evidence: Sequence[Evidence]) -> list[str]:
    """Return the conversation ids behind ranked evidence, best rank first.

    A conversation appears once, at its best rank: a system returning five
    passages of one conversation must not spend five of the k slots another
    system spends on five distinct conversations.

    Args:
        evidence: The adapter's hits, already in rank order.

    Returns:
        Conversation ids in rank order, without repetition.
    """
    ordered: list[str] = []
    seen: set[str] = set()
    for hit in evidence:
        for raw in hit.source_ids:
            source_id = normalize_source_id(raw)
            if source_id not in seen:
                seen.add(source_id)
                ordered.append(source_id)
    return ordered
