"""What an adapter returns for a question."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    """One ranked piece of evidence a memory system offers.

    A system that rewrites memories may have no source conversation at all.
    That is not a defect, and `source_ids` is empty for it: such a system
    simply does not appear in Track R.

    Two of the four fields are recorded and not scored. Nothing in the harness
    reads `native_id` or `timestamp` today: they are written into `raw.jsonl`
    so a run stays diagnosable and so the later tracks have the data they need
    without a contract break. `native_id` is what an operator quotes back at
    the system under test to find the item again. `timestamp` is for the
    temporal-contradiction stratum, which has to know which version of a
    reversed fact a system returned, so it must be an ISO 8601 instant with an
    explicit offset - `2026-03-14T09:12:00+00:00` - and not a free-form date,
    or it will not be comparable across systems when that track arrives.

    Attributes:
        text: The evidence itself, which Track A reads.
        native_id: The system's own identifier for this item. Recorded, not
            scored.
        source_ids: Conversation ids this evidence derives from, if any.
            Matched verbatim against the corpus `conversation_id`, with
            exactly one leading `synthesis/` forgiven and nothing else
            normalised.
        timestamp: ISO 8601 instant with an explicit offset that the evidence
            refers to, if the system knows it. Recorded, not scored.
    """

    text: str
    native_id: str
    source_ids: tuple[str, ...]
    timestamp: str | None
