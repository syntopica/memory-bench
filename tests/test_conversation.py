from dataclasses import FrozenInstanceError

import pytest

from membench.conversation import Conversation
from membench.message import Message


def test_body_joins_message_contents_in_order():
    conversation = Conversation(
        conversation_id="c1",
        started_at="2026-01-05T09:00:00Z",
        messages=(
            Message(role="user", content="we are reverting WAL", timestamp="2026-01-05T09:00:00Z"),
            Message(role="assistant", content="noted", timestamp="2026-01-05T09:01:00Z"),
        ),
    )
    assert conversation.body == "we are reverting WAL\nnoted"


def test_conversation_is_frozen():
    conversation = Conversation(
        conversation_id="c1", started_at="2026-01-05T09:00:00Z", messages=()
    )
    with pytest.raises(FrozenInstanceError):
        conversation.conversation_id = "c2"
