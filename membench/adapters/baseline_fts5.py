"""The floor: SQLite FTS5 over the joined conversation text."""

import sqlite3
import time
from collections.abc import Sequence
from pathlib import Path

from membench.conversation import Conversation
from membench.evidence import Evidence
from membench.fts5_query import fts5_query
from membench.ingest_report import IngestReport


class BaselineFts5Adapter:
    """Lexical retrieval with no model, no embedding and no extraction.

    Without this floor no other number means anything: it is how much a
    sophisticated system actually adds over full-text search.
    """

    def __init__(self, database: Path) -> None:
        """Store where the index lives; open nothing yet.

        Args:
            database: Path of the SQLite file this adapter owns.
        """
        self._database = database
        self._connection: sqlite3.Connection | None = None

    def setup(self) -> None:
        """Create an empty FTS5 table, replacing any previous index."""
        self._database.unlink(missing_ok=True)
        self._connection = sqlite3.connect(self._database)
        self._connection.execute(
            "CREATE VIRTUAL TABLE conversations USING fts5(conversation_id UNINDEXED, body)"
        )

    def ingest(self, corpus: Sequence[Conversation]) -> IngestReport:
        """Index one row per conversation and report time and index size.

        Args:
            corpus: The conversations, ingested in the order given.

        Returns:
            The measured cost. Token counts are zero: this system calls no model.
        """
        connection = self._require_connection()
        started = time.monotonic()
        connection.executemany(
            "INSERT INTO conversations (conversation_id, body) VALUES (?, ?)",
            [(conversation.conversation_id, conversation.body) for conversation in corpus],
        )
        connection.commit()
        seconds = time.monotonic() - started
        return IngestReport(
            seconds=seconds,
            index_bytes=self._database.stat().st_size,
            input_tokens=0,
            output_tokens=0,
        )

    def query(self, question: str, k: int) -> list[Evidence]:
        """Return the best k conversations FTS5 ranks for the question.

        Args:
            question: The question as a person asked it.
            k: How many hits to return at most.

        Returns:
            Evidence in rank order, each pointing at one conversation.
        """
        connection = self._require_connection()
        rows = connection.execute(
            "SELECT conversation_id, body FROM conversations "
            "WHERE conversations MATCH ? ORDER BY rank LIMIT ?",
            (fts5_query(question), k),
        ).fetchall()
        return [
            Evidence(
                text=body,
                native_id=conversation_id,
                source_ids=(conversation_id,),
                timestamp=None,
            )
            for conversation_id, body in rows
        ]

    def teardown(self) -> None:
        """Close the connection, leaving the index file in place."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _require_connection(self) -> sqlite3.Connection:
        """Return the open connection, or fail loudly if setup was skipped."""
        if self._connection is None:
            raise RuntimeError("setup() must run before ingest() or query()")
        return self._connection
