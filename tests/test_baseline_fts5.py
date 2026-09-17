from pathlib import Path

from membench.adapters.baseline_fts5 import BaselineFts5Adapter
from membench.conversation import Conversation
from membench.message import Message


def _corpus() -> list[Conversation]:
    return [
        Conversation(
            conversation_id="c1",
            started_at="2026-01-05T09:00:00Z",
            messages=(
                Message(role="user", content="montamos FTS5", timestamp="2026-01-05T09:00:00Z"),
            ),
        ),
        Conversation(
            conversation_id="c5",
            started_at="2026-06-14T16:00:00Z",
            messages=(
                Message(role="user", content="revertimos WAL", timestamp="2026-06-14T16:00:00Z"),
            ),
        ),
    ]


def test_ingest_reports_time_and_index_size(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    report = adapter.ingest(_corpus())
    adapter.teardown()
    assert report.seconds >= 0.0
    assert report.index_bytes > 0
    assert report.input_tokens == 0
    assert report.output_tokens == 0


def test_query_returns_evidence_whose_source_is_the_conversation(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("revertimos WAL", 10)
    adapter.teardown()
    assert hits[0].source_ids == ("c5",)
    assert "revertimos" in hits[0].text


def test_query_respects_k(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("montamos OR revertimos", 1)
    adapter.teardown()
    assert len(hits) == 1


def test_a_question_with_punctuation_does_not_raise(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("¿por que se revirtio WAL?", 10)
    adapter.teardown()
    assert hits[0].source_ids == ("c5",)


def test_a_question_containing_fts5_operators_does_not_raise(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("AND OR NOT NEAR revertimos", 10)
    adapter.teardown()
    assert hits[0].source_ids == ("c5",)
