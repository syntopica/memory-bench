import json
from pathlib import Path

import pytest

from membench.load_corpus import load_corpus


def test_loads_a_conversation_with_its_messages(tmp_path: Path):
    path = tmp_path / "corpus.jsonl"
    path.write_text(
        json.dumps(
            {
                "conversation_id": "c1",
                "started_at": "2026-01-05T09:00:00Z",
                "messages": [
                    {"role": "user", "content": "hola", "timestamp": "2026-01-05T09:00:00Z"}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    corpus = load_corpus(path)
    assert len(corpus) == 1
    assert corpus[0].conversation_id == "c1"
    assert corpus[0].messages[0].content == "hola"


def test_blank_lines_are_skipped(tmp_path: Path):
    path = tmp_path / "corpus.jsonl"
    path.write_text(
        json.dumps({"conversation_id": "c1", "started_at": "2026-01-05T09:00:00Z", "messages": []})
        + "\n\n",
        encoding="utf-8",
    )
    assert len(load_corpus(path)) == 1


def test_duplicate_conversation_ids_are_rejected(tmp_path: Path):
    line = json.dumps(
        {"conversation_id": "c1", "started_at": "2026-01-05T09:00:00Z", "messages": []}
    )
    path = tmp_path / "corpus.jsonl"
    path.write_text(f"{line}\n{line}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate conversation id: c1"):
        load_corpus(path)
