"""One message inside a conversation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Message:
    """A single turn, as the canonical archive stores it.

    Attributes:
        role: Who spoke, normally "user" or "assistant".
        content: The text of the turn.
        timestamp: ISO-8601 instant the turn was written.
    """

    role: str
    content: str
    timestamp: str
