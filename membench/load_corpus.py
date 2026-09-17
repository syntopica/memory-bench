"""Read a corpus of conversations from JSONL."""

import json
from pathlib import Path

from membench.conversation import Conversation
from membench.message import Message


def load_corpus(path: Path) -> list[Conversation]:
    """Return the conversations one JSON object per line holds.

    Args:
        path: The corpus JSONL file.

    Returns:
        The conversations, in file order.

    Raises:
        ValueError: If a conversation id appears twice, which would make the
            scored answer ambiguous.
    """
    conversations: list[Conversation] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        conversation_id = record["conversation_id"]
        if conversation_id in seen:
            raise ValueError(f"duplicate conversation id: {conversation_id}")
        seen.add(conversation_id)
        conversations.append(
            Conversation(
                conversation_id=conversation_id,
                started_at=record["started_at"],
                messages=tuple(
                    Message(
                        role=message["role"],
                        content=message["content"],
                        timestamp=message["timestamp"],
                    )
                    for message in record["messages"]
                ),
            )
        )
    return conversations
