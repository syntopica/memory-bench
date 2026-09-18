from pathlib import Path

from membench.adapters.baseline_fts5_adapter import BaselineFts5Adapter
from membench.conversation import Conversation
from membench.count_tokens import count_tokens
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
        Conversation(
            conversation_id="c9",
            started_at="2026-07-01T10:00:00Z",
            messages=(
                Message(
                    role="user",
                    content="cambiamos la configuración del índice",
                    timestamp="2026-07-01T10:00:00Z",
                ),
            ),
        ),
    ]


def test_ingest_reports_time_and_bytes_persisted(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    report = adapter.ingest(_corpus())
    adapter.teardown()
    assert report.seconds >= 0.0
    assert report.persisted_bytes > 0
    assert report.input_tokens == 0
    assert report.output_tokens == 0


def test_query_returns_evidence_whose_source_is_the_conversation(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("revertimos WAL", 10, None)
    adapter.teardown()
    assert hits[0].source_ids == ("c5",)
    assert "revertimos" in hits[0].text


def test_query_respects_k(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("montamos OR revertimos", 1, None)
    adapter.teardown()
    assert len(hits) == 1


def test_a_question_with_punctuation_does_not_raise(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("¿por que se revirtio WAL?", 10, None)
    adapter.teardown()
    assert hits[0].source_ids == ("c5",)


def test_a_question_containing_fts5_operators_does_not_raise(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("AND OR NOT NEAR revertimos", 10, None)
    adapter.teardown()
    assert hits[0].source_ids == ("c5",)


def test_an_unaccented_query_matches_an_accented_document(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("configuracion", 10, None)
    adapter.teardown()
    assert [hit.source_ids for hit in hits] == [("c9",)]


def test_an_accented_query_matches_an_unaccented_document(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "baseline.db")
    adapter.setup()
    adapter.ingest(_corpus())
    hits = adapter.query("revértimos", 10, None)
    adapter.teardown()
    assert [hit.source_ids for hit in hits] == [("c5",)]


def test_a_budget_drops_evidence_from_the_end(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "index.db")
    adapter.setup()
    adapter.ingest(
        [
            Conversation(
                conversation_id="c1",
                started_at="2026-01-05T09:00:00Z",
                messages=(
                    Message(role="user", content="wal wal wal", timestamp="2026-01-05T09:00:00Z"),
                ),
            ),
            Conversation(
                conversation_id="c2",
                started_at="2026-01-06T09:00:00Z",
                messages=(
                    Message(role="user", content="wal wal wal", timestamp="2026-01-06T09:00:00Z"),
                ),
            ),
        ]
    )
    unbounded = adapter.query("wal", 10, None)
    assert len(unbounded) == 2

    bounded = adapter.query("wal", 10, token_budget=3)
    assert len(bounded) == 1
    assert sum(count_tokens(piece.text) for piece in bounded) <= 3
    adapter.teardown()


def test_a_budget_smaller_than_the_first_hit_returns_nothing(tmp_path: Path):
    adapter = BaselineFts5Adapter(tmp_path / "index.db")
    adapter.setup()
    adapter.ingest(
        [
            Conversation(
                conversation_id="c1",
                started_at="2026-01-05T09:00:00Z",
                messages=(
                    Message(role="user", content="wal wal wal", timestamp="2026-01-05T09:00:00Z"),
                ),
            ),
        ]
    )
    assert adapter.query("wal", 10, token_budget=1) == []
    adapter.teardown()
