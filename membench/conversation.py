"""One conversation of the corpus, the granularity Track R scores at."""

from dataclasses import dataclass

from membench.message import Message


@dataclass(frozen=True, slots=True)
class Conversation:
    """A conversation and the messages it holds.

    Attributes:
        conversation_id: The identity Track R scores against.
        started_at: ISO-8601 instant of the first message.
        messages: The turns, in chronological order.
    """

    conversation_id: str
    started_at: str
    messages: tuple[Message, ...]

    @property
    def body(self) -> str:
        """Return every message content joined by newlines, in order."""
        return "\n".join(message.content for message in self.messages)
