"""What an adapter returns for a question."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    """One ranked piece of evidence a memory system offers.

    A system that rewrites memories may have no source conversation at all.
    That is not a defect, and `source_ids` is empty for it: such a system
    simply does not appear in Track R.

    Attributes:
        text: The evidence itself, which Track A reads.
        native_id: The system's own identifier for this item.
        source_ids: Conversation ids this evidence derives from, if any.
        timestamp: ISO-8601 instant the evidence refers to, if the system knows it.
    """

    text: str
    native_id: str
    source_ids: tuple[str, ...]
    timestamp: str | None
