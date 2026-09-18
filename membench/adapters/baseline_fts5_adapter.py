"""The floor: SQLite FTS5 over the joined conversation text."""

import sqlite3
import time
from collections.abc import Sequence
from pathlib import Path

from membench.conversation import Conversation
from membench.count_tokens import count_tokens
from membench.evidence import Evidence
from membench.fts5_query import fts5_query
from membench.ingest_report import IngestReport


class BaselineFts5Adapter:
    """Lexical retrieval with no model, no embedding and no extraction.

    Without this floor no other number means anything: it is how much a
    sophisticated system actually adds over full-text search.
    """

    def __init__(self, workspace: Path) -> None:
        """Store the workspace this adapter owns; open nothing yet.

        Args:
            workspace: Directory this adapter owns exclusively. Its SQLite
                file is placed inside it, at a location this adapter decides.
        """
        self._database = workspace / "index.db"
        self._connection: sqlite3.Connection | None = None

    def setup(self) -> None:
        """Create an empty FTS5 table, replacing any previous index.

        The tokenizer is pinned rather than inherited. FTS5's default
        `remove_diacritics` setting varies with the SQLite build, and this
        benchmark's headline claim is a non-English corpus: an unpinned
        tokenizer would move `configuración` against `configuracion` between
        two machines with nothing in the artifact to show it. The manifest
        records the SQLite version alongside.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        self._database.unlink(missing_ok=True)
        self._connection = sqlite3.connect(self._database)
        self._connection.execute(
            "CREATE VIRTUAL TABLE conversations USING fts5("
            "conversation_id UNINDEXED, body, "
            "tokenize='unicode61 remove_diacritics 2')"
        )

    def ingest(self, corpus: Sequence[Conversation]) -> IngestReport:
        """Index one row per conversation and report time and bytes persisted.

        Args:
            corpus: The conversations, ingested in the order given.

        Returns:
            The measured cost. The byte count is the whole SQLite file, the
            corpus copy in FTS5's content table included. Token counts are
            zero: this system calls no model.
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
            persisted_bytes=self._database.stat().st_size,
            input_tokens=0,
            output_tokens=0,
        )

    def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
        """Return the best k conversations FTS5 ranks for the question.

        Args:
            question: The question as a person asked it.
            k: How many hits to return at most.
            token_budget: The harness's token budget, or None for unbounded.
                The longest prefix of the ranking that fits is returned,
                dropping from the end.

        Returns:
            Evidence in rank order, each pointing at one conversation.
        """
        connection = self._require_connection()
        rows = connection.execute(
            "SELECT conversation_id, body FROM conversations "
            "WHERE conversations MATCH ? ORDER BY rank LIMIT ?",
            (fts5_query(question), k),
        ).fetchall()
        hits = [
            Evidence(
                text=body,
                native_id=conversation_id,
                source_ids=(conversation_id,),
                timestamp=None,
            )
            for conversation_id, body in rows
        ]
        return self._within_budget(hits, token_budget)

    @staticmethod
    def _within_budget(hits: list[Evidence], token_budget: int | None) -> list[Evidence]:
        """Return the longest prefix of `hits` whose token count fits the budget."""
        if token_budget is None:
            return hits
        kept: list[Evidence] = []
        spent = 0
        for hit in hits:
            cost = count_tokens(hit.text)
            if spent + cost > token_budget:
                break
            kept.append(hit)
            spent += cost
        return kept

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
