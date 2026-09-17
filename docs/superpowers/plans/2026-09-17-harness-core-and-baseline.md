# memory-bench Phase 1, Plan 1: Harness Core and the Dumb Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A runnable Track R harness that scores a memory system's source discovery over a corpus, proven end to end against a SQLite FTS5 baseline, with no VM, no gateway and no model call anywhere in the test path.

**Architecture:** A memory system is a `MemoryAdapter` with four methods. The harness loads a corpus of conversations and a question set, asks the adapter for ranked `Evidence`, maps each hit to its source conversation, and scores recall@k and reciprocal rank. The baseline adapter is SQLite FTS5 over the joined message text — the floor every sophisticated system has to beat. Everything is pure Python over JSONL files on disk; the later plans (gateway + mem0, Atrium + the Track A reader) plug into the same `MemoryAdapter` without changing the core.

**Tech Stack:** Python 3.12+, uv, pytest, stdlib `sqlite3` with FTS5, `syntopica-codeality-py` as the quality gate.

**Spec:** `docs/superpowers/specs/2026-09-17-memory-bench-design.md`

## Global Constraints

- Python `>=3.12`. Dependency manager is `uv`; every command runs as `uv run ...`.
- One exported unit and one responsibility per file. Helpers, secondary types and constants go in their own file and are imported explicitly.
- `max-file-lines = 150` for source, `300` for tests, enforced by `uv run codeality-py gate`.
- Coverage threshold `80`. This is a new repository with no ratchet debt; never lower it.
- All code, comments, identifiers, docstrings and commit messages in English.
- Track R is labelled "source discovery" in every user-facing string. It is never called memory quality, accuracy, or recall of facts.
- Question JSONL keys are `question`, `answer_conversation_id` and `strata`, matching `~/p/atrium/benchmarks/acceptance/README.md`, so labelled sets are interchangeable between the two repositories.
- No LLM call, no network access and no Docker in this plan. A test that needs any of them belongs to a later plan.
- Never `git push`; this repository has no remote yet.

---

### Task 1: Repository scaffold and the core value types

**Files:**
- Create: `pyproject.toml`
- Create: `codeality-py.toml`
- Create: `membench/__init__.py`
- Create: `membench/message.py`
- Create: `membench/conversation.py`
- Create: `membench/evidence.py`
- Create: `membench/ingest_report.py`
- Test: `tests/test_conversation.py`
- Test: `tests/test_evidence.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Message(role: str, content: str, timestamp: str)`, `Conversation(conversation_id: str, started_at: str, messages: tuple[Message, ...])` with property `body -> str`, `Evidence(text: str, native_id: str, source_ids: tuple[str, ...], timestamp: str | None)`, `IngestReport(seconds: float, index_bytes: int, input_tokens: int, output_tokens: int)`.

- [ ] **Step 1: Write the failing tests**

`tests/test_conversation.py`:

```python
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
    conversation = Conversation(conversation_id="c1", started_at="2026-01-05T09:00:00Z", messages=())
    with pytest.raises(FrozenInstanceError):
        conversation.conversation_id = "c2"
```

Add at the top of that file:

```python
import pytest
from dataclasses import FrozenInstanceError
```

`tests/test_evidence.py`:

```python
from membench.evidence import Evidence
from membench.ingest_report import IngestReport


def test_evidence_carries_text_native_id_and_sources():
    evidence = Evidence(
        text="we are reverting WAL",
        native_id="row-7",
        source_ids=("c1",),
        timestamp="2026-01-05T09:00:00Z",
    )
    assert evidence.text == "we are reverting WAL"
    assert evidence.native_id == "row-7"
    assert evidence.source_ids == ("c1",)


def test_evidence_allows_no_provenance():
    evidence = Evidence(text="a consolidated memory", native_id="m-1", source_ids=(), timestamp=None)
    assert evidence.source_ids == ()


def test_ingest_report_holds_cost_and_size():
    report = IngestReport(seconds=1.5, index_bytes=4096, input_tokens=0, output_tokens=0)
    assert report.seconds == 1.5
    assert report.index_bytes == 4096
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/ -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench'`.

- [ ] **Step 3: Write the scaffold and the minimal implementation**

`pyproject.toml`:

```toml
[project]
name = "membench"
version = "0.1.0"
description = "A two-track benchmark for agent memory systems"
requires-python = ">=3.12"
dependencies = []

[project.scripts]
membench = "membench.cli:main"

[dependency-groups]
dev = ["pytest>=8.0", "syntopica-codeality-py>=0.2.2"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["A", "ARG", "B", "C4", "D", "DTZ", "E", "ERA", "F", "I", "N", "PL", "PTH", "RET", "RUF", "SIM", "UP", "W"]
ignore = ["D203", "D213", "E501", "D107"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D", "S101", "ARG", "PLR2004"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

`codeality-py.toml`:

```toml
# codeality-py configuration - https://github.com/syntopica/codeality
schema-version = 1
source-roots = ["membench"]
test-roots = ["tests"]
respect-gitignore = true
# New repository, no ratchet debt. Raise toward 90, never lower.
coverage-threshold = 80

[limits]
max-file-lines = 150
test-max-file-lines = 300

[roles]
data = []
registry = []
entrypoint = ["membench/cli.py"]
generated = []
namespace-init = ["membench/__init__.py"]
```

`membench/__init__.py`:

```python
"""A two-track benchmark for agent memory systems."""
```

`membench/message.py`:

```python
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
```

`membench/conversation.py`:

```python
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
```

`membench/evidence.py`:

```python
"""What an adapter returns for a question."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    """One ranked piece of evidence a memory system offers.

    A system that rewrites memories may have no source conversation at all.
    That is not a defect, and `source_ids` is empty for it: such a system
    simply does not appear in Track R.

    Attributes:
        text: The evidence itself, which Track A reads.
        native_id: The system's own identifier for this item.
        source_ids: Conversation ids this evidence derives from, if any.
        timestamp: ISO-8601 instant the evidence refers to, if the system knows it.
    """

    text: str
    native_id: str
    source_ids: tuple[str, ...]
    timestamp: str | None
```

`membench/ingest_report.py`:

```python
"""What ingesting a corpus cost a memory system."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IngestReport:
    """Measured cost of one ingestion.

    Token counts are counted, never priced: a monetary estimate is derived
    later and reported separately.

    Attributes:
        seconds: Wall-clock duration of the ingestion.
        index_bytes: Bytes of derived index the ingestion produced.
        input_tokens: Model input tokens the ingestion consumed, zero if none.
        output_tokens: Model output tokens the ingestion consumed, zero if none.
    """

    seconds: float
    index_bytes: int
    input_tokens: int
    output_tokens: int
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/ -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml codeality-py.toml membench/ tests/ uv.lock
git commit -m "feat: core value types for the benchmark harness"
```

---

### Task 2: Source-id normalisation and ranked source extraction

**Files:**
- Create: `membench/normalize_source_id.py`
- Create: `membench/ranked_sources.py`
- Test: `tests/test_normalize_source_id.py`
- Test: `tests/test_ranked_sources.py`

**Interfaces:**
- Consumes: `Evidence` from Task 1.
- Produces: `normalize_source_id(raw: str) -> str`, `ranked_sources(evidence: Sequence[Evidence]) -> list[str]`.

Why this exists: Atrium's synthesis records carry `conversation_id = f"synthesis/{...}"` (`~/p/atrium/atrium/ingest/to_synthesis_records.py:33`). Without normalisation, a synthesis hit and a raw hit on the same conversation look like two different answers, and the scored rank is wrong. Deduplication matters for the same reason: one system returning five passages of the same conversation must not consume five of the k slots that another system spends on five distinct conversations.

- [ ] **Step 1: Write the failing tests**

`tests/test_normalize_source_id.py`:

```python
from membench.normalize_source_id import normalize_source_id


def test_strips_the_atrium_synthesis_namespace():
    assert normalize_source_id("synthesis/abc123") == "abc123"


def test_leaves_a_plain_id_alone():
    assert normalize_source_id("abc123") == "abc123"


def test_strips_only_the_leading_namespace():
    assert normalize_source_id("synthesis/synthesis/abc") == "synthesis/abc"


def test_unknown_namespace_is_left_intact():
    assert normalize_source_id("notes/abc123") == "notes/abc123"
```

`tests/test_ranked_sources.py`:

```python
from membench.evidence import Evidence
from membench.ranked_sources import ranked_sources


def _evidence(native_id: str, *source_ids: str) -> Evidence:
    return Evidence(text="t", native_id=native_id, source_ids=source_ids, timestamp=None)


def test_returns_sources_in_rank_order():
    assert ranked_sources([_evidence("a", "c1"), _evidence("b", "c2")]) == ["c1", "c2"]


def test_deduplicates_keeping_the_best_rank():
    hits = [_evidence("a", "c1"), _evidence("b", "c1"), _evidence("c", "c2")]
    assert ranked_sources(hits) == ["c1", "c2"]


def test_normalizes_the_synthesis_namespace_before_deduplicating():
    hits = [_evidence("a", "synthesis/c1"), _evidence("b", "c1")]
    assert ranked_sources(hits) == ["c1"]


def test_one_evidence_with_several_sources_yields_each_in_order():
    assert ranked_sources([_evidence("a", "c1", "c2")]) == ["c1", "c2"]


def test_evidence_without_provenance_contributes_nothing():
    assert ranked_sources([_evidence("a")]) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_normalize_source_id.py tests/test_ranked_sources.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.normalize_source_id'`.

- [ ] **Step 3: Write the minimal implementation**

`membench/normalize_source_id.py`:

```python
"""Map a system's source identifier onto the corpus conversation id."""

_SYNTHESIS_NAMESPACE = "synthesis/"


def normalize_source_id(raw: str) -> str:
    """Return the corpus conversation id a source identifier refers to.

    Atrium writes synthesis records under a `synthesis/<conversation id>`
    namespace, so a synthesis hit and a raw hit on the same conversation must
    collapse to one answer before ranking.

    Args:
        raw: The source identifier the adapter reported.

    Returns:
        The conversation id, with a single leading synthesis namespace removed.
    """
    if raw.startswith(_SYNTHESIS_NAMESPACE):
        return raw[len(_SYNTHESIS_NAMESPACE) :]
    return raw
```

`membench/ranked_sources.py`:

```python
"""Reduce ranked evidence to the ranked, deduplicated conversations behind it."""

from collections.abc import Sequence

from membench.evidence import Evidence
from membench.normalize_source_id import normalize_source_id


def ranked_sources(evidence: Sequence[Evidence]) -> list[str]:
    """Return the conversation ids behind ranked evidence, best rank first.

    A conversation appears once, at its best rank: a system returning five
    passages of one conversation must not spend five of the k slots another
    system spends on five distinct conversations.

    Args:
        evidence: The adapter's hits, already in rank order.

    Returns:
        Conversation ids in rank order, without repetition.
    """
    ordered: list[str] = []
    seen: set[str] = set()
    for hit in evidence:
        for raw in hit.source_ids:
            source_id = normalize_source_id(raw)
            if source_id not in seen:
                seen.add(source_id)
                ordered.append(source_id)
    return ordered
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_normalize_source_id.py tests/test_ranked_sources.py -v`
Expected: PASS, 9 tests.

- [ ] **Step 5: Commit**

```bash
git add membench/normalize_source_id.py membench/ranked_sources.py tests/
git commit -m "feat: normalize and deduplicate the sources behind ranked evidence"
```

---

### Task 3: The Track R metrics

**Files:**
- Create: `membench/recall_at_k.py`
- Create: `membench/reciprocal_rank.py`
- Test: `tests/test_recall_at_k.py`
- Test: `tests/test_reciprocal_rank.py`

**Interfaces:**
- Consumes: nothing beyond the stdlib.
- Produces: `recall_at_k(ranked: Sequence[str], answer_id: str, k: int) -> float`, `reciprocal_rank(ranked: Sequence[str], answer_id: str) -> float`.

- [ ] **Step 1: Write the failing tests**

`tests/test_recall_at_k.py`:

```python
import pytest

from membench.recall_at_k import recall_at_k


def test_hit_inside_k_scores_one():
    assert recall_at_k(["c1", "c2", "c3"], "c2", 3) == 1.0


def test_hit_outside_k_scores_zero():
    assert recall_at_k(["c1", "c2", "c3"], "c3", 2) == 0.0


def test_absent_answer_scores_zero():
    assert recall_at_k(["c1", "c2"], "c9", 10) == 0.0


def test_empty_ranking_scores_zero():
    assert recall_at_k([], "c1", 10) == 0.0


def test_k_must_be_positive():
    with pytest.raises(ValueError, match="k must be positive"):
        recall_at_k(["c1"], "c1", 0)
```

`tests/test_reciprocal_rank.py`:

```python
from membench.reciprocal_rank import reciprocal_rank


def test_first_position_scores_one():
    assert reciprocal_rank(["c1", "c2"], "c1") == 1.0


def test_third_position_scores_one_third():
    assert reciprocal_rank(["c1", "c2", "c3"], "c3") == pytest.approx(1 / 3)


def test_absent_answer_scores_zero():
    assert reciprocal_rank(["c1", "c2"], "c9") == 0.0


def test_empty_ranking_scores_zero():
    assert reciprocal_rank([], "c1") == 0.0
```

Add at the top of `tests/test_reciprocal_rank.py`:

```python
import pytest
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_recall_at_k.py tests/test_reciprocal_rank.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.recall_at_k'`.

- [ ] **Step 3: Write the minimal implementation**

`membench/recall_at_k.py`:

```python
"""Whether the labelled answer conversation appears in the top k."""

from collections.abc import Sequence


def recall_at_k(ranked: Sequence[str], answer_id: str, k: int) -> float:
    """Return 1.0 when the answer conversation is within the first k, else 0.0.

    Each question has exactly one labelled relevant conversation, so recall
    here is a hit rate; it is named recall because that is what the literature
    this is compared against reports.

    Args:
        ranked: Conversation ids in rank order, deduplicated.
        answer_id: The labelled answer conversation.
        k: How deep into the ranking to look.

    Returns:
        1.0 on a hit within k, 0.0 otherwise.

    Raises:
        ValueError: If k is not positive.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    return 1.0 if answer_id in ranked[:k] else 0.0
```

`membench/reciprocal_rank.py`:

```python
"""Reciprocal of the rank at which the labelled answer conversation appears."""

from collections.abc import Sequence


def reciprocal_rank(ranked: Sequence[str], answer_id: str) -> float:
    """Return 1/rank of the answer conversation, or 0.0 when it is absent.

    Args:
        ranked: Conversation ids in rank order, deduplicated.
        answer_id: The labelled answer conversation.

    Returns:
        The reciprocal of the 1-based rank, or 0.0 when the answer is missing.
    """
    for position, source_id in enumerate(ranked, start=1):
        if source_id == answer_id:
            return 1.0 / position
    return 0.0
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_recall_at_k.py tests/test_reciprocal_rank.py -v`
Expected: PASS, 9 tests.

- [ ] **Step 5: Commit**

```bash
git add membench/recall_at_k.py membench/reciprocal_rank.py tests/
git commit -m "feat: recall@k and reciprocal rank for track R"
```

---

### Task 4: Corpus and question loaders, and the fixture corpus

**Files:**
- Create: `membench/question.py`
- Create: `membench/load_corpus.py`
- Create: `membench/load_questions.py`
- Create: `corpora/fixture/corpus.jsonl`
- Create: `corpora/fixture/questions.jsonl`
- Test: `tests/test_load_corpus.py`
- Test: `tests/test_load_questions.py`
- Test: `tests/test_fixture_corpus.py`

**Interfaces:**
- Consumes: `Conversation`, `Message` from Task 1.
- Produces: `Question(question_id: str, question: str, answer_conversation_id: str, strata: tuple[str, ...])`, `load_corpus(path: Path) -> list[Conversation]`, `load_questions(path: Path) -> list[Question]`.

The fixture corpus is not corpus A. It is six hand-written conversations whose only job is to prove the harness scores correctly, including one reversal pair so a system that returns the superseded version can be seen doing it. Corpus A is generated in a later plan.

- [ ] **Step 1: Write the failing tests**

`tests/test_load_corpus.py`:

```python
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
```

`tests/test_load_questions.py`:

```python
import json
from pathlib import Path

import pytest

from membench.load_questions import load_questions


def test_loads_a_labelled_question(tmp_path: Path):
    path = tmp_path / "questions.jsonl"
    path.write_text(
        json.dumps(
            {
                "question_id": "q1",
                "question": "por que se revirtio WAL",
                "answer_conversation_id": "c1",
                "strata": ["es", "conversation", "overlap", "recent"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    questions = load_questions(path)
    assert questions[0].question_id == "q1"
    assert questions[0].answer_conversation_id == "c1"
    assert questions[0].strata == ("es", "conversation", "overlap", "recent")


def test_an_unlabelled_question_is_rejected(tmp_path: Path):
    path = tmp_path / "questions.jsonl"
    path.write_text(
        json.dumps({"question_id": "q1", "question": "x", "answer_conversation_id": "", "strata": []})
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="question q1 has no answer_conversation_id"):
        load_questions(path)
```

`tests/test_fixture_corpus.py`:

```python
from pathlib import Path

from membench.load_corpus import load_corpus
from membench.load_questions import load_questions

FIXTURE = Path(__file__).resolve().parent.parent / "corpora" / "fixture"


def test_every_question_points_at_a_conversation_in_the_corpus():
    corpus_ids = {conversation.conversation_id for conversation in load_corpus(FIXTURE / "corpus.jsonl")}
    for question in load_questions(FIXTURE / "questions.jsonl"):
        assert question.answer_conversation_id in corpus_ids


def test_the_fixture_holds_a_reversal_pair():
    questions = load_questions(FIXTURE / "questions.jsonl")
    assert any("temporal-contradiction" in question.strata for question in questions)


def test_the_fixture_covers_both_languages():
    strata = {stratum for question in load_questions(FIXTURE / "questions.jsonl") for stratum in question.strata}
    assert {"es", "en"} <= strata
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_load_corpus.py tests/test_load_questions.py tests/test_fixture_corpus.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.load_corpus'`.

- [ ] **Step 3: Write the minimal implementation**

`membench/question.py`:

```python
"""One labelled question of an evaluation set."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Question:
    """A question and the conversation a human confirmed answers it.

    Attributes:
        question_id: Stable identity, used in the raw results.
        question: The question text, as a person would ask it.
        answer_conversation_id: The labelled answer conversation.
        strata: Tags such as "es", "conversation", "no-overlap", "recent",
            "temporal-contradiction", used for descriptive breakdowns only.
    """

    question_id: str
    question: str
    answer_conversation_id: str
    strata: tuple[str, ...]
```

`membench/load_corpus.py`:

```python
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
```

`membench/load_questions.py`:

```python
"""Read a labelled question set from JSONL."""

import json
from pathlib import Path

from membench.question import Question


def load_questions(path: Path) -> list[Question]:
    """Return the labelled questions one JSON object per line holds.

    The keys are the ones Atrium's acceptance protocol already uses, so a
    labelled set moves between the two repositories unchanged.

    Args:
        path: The question JSONL file.

    Returns:
        The questions, in file order.

    Raises:
        ValueError: If a question carries no answer conversation, which would
            silently score as a miss for every system.
    """
    questions: list[Question] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        answer_conversation_id = record["answer_conversation_id"]
        if not answer_conversation_id:
            raise ValueError(f"question {record['question_id']} has no answer_conversation_id")
        questions.append(
            Question(
                question_id=record["question_id"],
                question=record["question"],
                answer_conversation_id=answer_conversation_id,
                strata=tuple(record["strata"]),
            )
        )
    return questions
```

`corpora/fixture/corpus.jsonl` — six conversations, one per line. `c3` and `c5` are the reversal pair: `c3` adopts WAL, `c5` reverts it, and the question about the current state must resolve to `c5`.

```jsonl
{"conversation_id": "c1", "started_at": "2026-01-05T09:00:00Z", "messages": [{"role": "user", "content": "Vamos a montar el indice de conversaciones en SQLite con FTS5", "timestamp": "2026-01-05T09:00:00Z"}, {"role": "assistant", "content": "De acuerdo, FTS5 cubre la busqueda lexica sin dependencias externas", "timestamp": "2026-01-05T09:01:00Z"}]}
{"conversation_id": "c2", "started_at": "2026-02-11T14:00:00Z", "messages": [{"role": "user", "content": "The deploy pipeline failed because the runner ran out of disk", "timestamp": "2026-02-11T14:00:00Z"}, {"role": "assistant", "content": "Pruning the image cache freed 40 GB and the pipeline went green", "timestamp": "2026-02-11T14:05:00Z"}]}
{"conversation_id": "c3", "started_at": "2026-03-02T10:00:00Z", "messages": [{"role": "user", "content": "Activamos WAL en la base de datos para que las lecturas no bloqueen", "timestamp": "2026-03-02T10:00:00Z"}, {"role": "assistant", "content": "WAL activado, las escrituras concurrentes mejoran", "timestamp": "2026-03-02T10:02:00Z"}]}
{"conversation_id": "c4", "started_at": "2026-04-20T08:30:00Z", "messages": [{"role": "user", "content": "Marta prefers reviews in the morning and never before coffee", "timestamp": "2026-04-20T08:30:00Z"}, {"role": "assistant", "content": "Noted, review requests go out after 10:00 for her", "timestamp": "2026-04-20T08:31:00Z"}]}
{"conversation_id": "c5", "started_at": "2026-06-14T16:00:00Z", "messages": [{"role": "user", "content": "Revertimos lo de antes: el fichero de journal crecia sin limite en el disco compartido", "timestamp": "2026-06-14T16:00:00Z"}, {"role": "assistant", "content": "Vuelta al modo journal por defecto, el disco deja de llenarse", "timestamp": "2026-06-14T16:04:00Z"}]}
{"conversation_id": "c6", "started_at": "2026-08-01T11:00:00Z", "messages": [{"role": "user", "content": "The nightly export crashed at 3am for the third time this week", "timestamp": "2026-08-01T11:00:00Z"}, {"role": "assistant", "content": "The cron overlapped with the backup window; moving it to 05:00 fixed it", "timestamp": "2026-08-01T11:10:00Z"}]}
```

`corpora/fixture/questions.jsonl`:

```jsonl
{"question_id": "q1", "question": "que motor de busqueda lexica usamos para el indice", "answer_conversation_id": "c1", "strata": ["es", "conversation", "overlap", "old"]}
{"question_id": "q2", "question": "why did the deploy pipeline fail in February", "answer_conversation_id": "c2", "strata": ["en", "conversation", "overlap", "old"]}
{"question_id": "q3", "question": "en que modo esta la base de datos ahora mismo", "answer_conversation_id": "c5", "strata": ["es", "conversation", "no-overlap", "recent", "temporal-contradiction"]}
{"question_id": "q4", "question": "when should review requests go to Marta", "answer_conversation_id": "c4", "strata": ["en", "conversation", "overlap", "old"]}
{"question_id": "q5", "question": "por que se dejo de usar WAL", "answer_conversation_id": "c5", "strata": ["es", "conversation", "no-overlap", "recent"]}
{"question_id": "q6", "question": "what fixed the nightly export crashes", "answer_conversation_id": "c6", "strata": ["en", "conversation", "overlap", "recent"]}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_load_corpus.py tests/test_load_questions.py tests/test_fixture_corpus.py -v`
Expected: PASS, 8 tests.

- [ ] **Step 5: Commit**

```bash
git add membench/question.py membench/load_corpus.py membench/load_questions.py corpora/ tests/
git commit -m "feat: corpus and question loaders, and a six-conversation fixture"
```

---

### Task 5: The FTS5 query builder

**Files:**
- Create: `membench/fts5_query.py`
- Test: `tests/test_fts5_query.py`

**Interfaces:**
- Consumes: nothing beyond the stdlib.
- Produces: `fts5_query(text: str) -> str`.

Why this is its own task: FTS5 `MATCH` takes a query language, not a sentence. A raw question containing `?`, `¿`, a hyphen or a quote is either a syntax error or, worse, silently reinterpreted — `sqlite3.OperationalError: fts5: syntax error near "?"`. The baseline would then score zero for a reason that has nothing to do with retrieval, and the whole comparison would rest on it.

- [ ] **Step 1: Write the failing test**

`tests/test_fts5_query.py`:

```python
from membench.fts5_query import fts5_query


def test_tokens_are_quoted_and_ored():
    assert fts5_query("wal reverted") == '"wal" OR "reverted"'


def test_punctuation_is_dropped():
    assert fts5_query("¿por que se revirtio WAL?") == '"por" OR "que" OR "se" OR "revirtio" OR "wal"'


def test_accents_are_preserved():
    assert fts5_query("configuración") == '"configuración"'


def test_embedded_quotes_cannot_escape_the_term():
    assert fts5_query('a "b" c') == '"a" OR "b" OR "c"'


def test_a_query_with_no_usable_token_matches_nothing():
    assert fts5_query("¿?") == '""'
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_fts5_query.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.fts5_query'`.

- [ ] **Step 3: Write the minimal implementation**

`membench/fts5_query.py`:

```python
"""Turn a natural-language question into a safe FTS5 MATCH expression."""

import re

_TOKEN = re.compile(r"\w+", re.UNICODE)


def fts5_query(text: str) -> str:
    """Return an FTS5 MATCH expression that ORs every word of the question.

    FTS5 MATCH takes a query language, not a sentence: a bare question mark or
    hyphen raises `sqlite3.OperationalError: fts5: syntax error`, which would
    score the baseline zero for a reason unrelated to retrieval. Each word is
    therefore quoted as a literal term, and OR keeps recall high, which is what
    a floor is for.

    Args:
        text: The question as a person asked it.

    Returns:
        A MATCH expression. A question with no word characters returns `""`,
        which is valid and matches nothing.
    """
    tokens = [token.lower() for token in _TOKEN.findall(text)]
    if not tokens:
        return '""'
    return " OR ".join(f'"{token}"' for token in tokens)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_fts5_query.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add membench/fts5_query.py tests/test_fts5_query.py
git commit -m "feat: build a safe FTS5 match expression from a question"
```

---

### Task 6: The dumb baseline adapter

**Files:**
- Create: `membench/adapter.py`
- Create: `membench/adapters/__init__.py`
- Create: `membench/adapters/baseline_fts5.py`
- Test: `tests/test_baseline_fts5.py`

**Interfaces:**
- Consumes: `Conversation`, `Evidence`, `IngestReport` from Task 1; `fts5_query` from Task 5.
- Produces: `MemoryAdapter` protocol with `setup() -> None`, `ingest(corpus: Sequence[Conversation]) -> IngestReport`, `query(question: str, k: int) -> list[Evidence]`, `teardown() -> None`; and `BaselineFts5Adapter(database: Path)` implementing it.

- [ ] **Step 1: Write the failing test**

`tests/test_baseline_fts5.py`:

```python
from pathlib import Path

from membench.adapters.baseline_fts5 import BaselineFts5Adapter
from membench.conversation import Conversation
from membench.message import Message


def _corpus() -> list[Conversation]:
    return [
        Conversation(
            conversation_id="c1",
            started_at="2026-01-05T09:00:00Z",
            messages=(Message(role="user", content="montamos FTS5", timestamp="2026-01-05T09:00:00Z"),),
        ),
        Conversation(
            conversation_id="c5",
            started_at="2026-06-14T16:00:00Z",
            messages=(Message(role="user", content="revertimos WAL", timestamp="2026-06-14T16:00:00Z"),),
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_baseline_fts5.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.adapters'`.

- [ ] **Step 3: Write the minimal implementation**

`membench/adapter.py`:

```python
"""The contract every memory system under test implements."""

from collections.abc import Sequence
from typing import Protocol

from membench.conversation import Conversation
from membench.evidence import Evidence
from membench.ingest_report import IngestReport


class MemoryAdapter(Protocol):
    """A memory system, as the harness sees it."""

    def setup(self) -> None:
        """Bring the system up, empty, ready to ingest."""
        ...

    def ingest(self, corpus: Sequence[Conversation]) -> IngestReport:
        """Ingest the corpus chronologically and report what it cost."""
        ...

    def query(self, question: str, k: int) -> list[Evidence]:
        """Return at most k pieces of evidence, best first."""
        ...

    def teardown(self) -> None:
        """Release every resource the system holds."""
        ...
```

`membench/adapters/__init__.py`:

```python
"""Adapters for the memory systems under test."""
```

`membench/adapters/baseline_fts5.py`:

```python
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
            Evidence(text=body, native_id=conversation_id, source_ids=(conversation_id,), timestamp=None)
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_baseline_fts5.py -v`
Expected: PASS, 4 tests.

- [ ] **Step 5: Commit**

```bash
git add membench/adapter.py membench/adapters/ tests/test_baseline_fts5.py
git commit -m "feat: SQLite FTS5 baseline adapter, the floor every system must beat"
```

---

### Task 7: Running Track R end to end

**Files:**
- Create: `membench/question_result.py`
- Create: `membench/run_track_r.py`
- Test: `tests/test_run_track_r.py`

**Interfaces:**
- Consumes: `MemoryAdapter` from Task 6, `Question` from Task 4, `ranked_sources` from Task 2, `recall_at_k` and `reciprocal_rank` from Task 3.
- Produces: `QuestionResult(question_id, strata, ranked_sources, recall_at_1, recall_at_5, recall_at_10, reciprocal_rank, seconds, evidence_texts)`, `run_track_r(adapter: MemoryAdapter, questions: Sequence[Question], k: int = 10) -> list[QuestionResult]`.

- [ ] **Step 1: Write the failing test**

`tests/test_run_track_r.py`:

```python
from membench.evidence import Evidence
from membench.question import Question
from membench.run_track_r import run_track_r


class _StubAdapter:
    def __init__(self, hits: list[Evidence]) -> None:
        self._hits = hits
        self.asked: list[tuple[str, int]] = []

    def setup(self) -> None: ...

    def ingest(self, corpus): ...

    def query(self, question: str, k: int) -> list[Evidence]:
        self.asked.append((question, k))
        return self._hits[:k]

    def teardown(self) -> None: ...


def _question() -> Question:
    return Question(
        question_id="q1",
        question="por que se revirtio WAL",
        answer_conversation_id="c5",
        strata=("es", "no-overlap"),
    )


def _evidence(conversation_id: str) -> Evidence:
    return Evidence(
        text=f"body of {conversation_id}",
        native_id=conversation_id,
        source_ids=(conversation_id,),
        timestamp=None,
    )


def test_a_first_place_hit_scores_one_everywhere():
    adapter = _StubAdapter([_evidence("c5"), _evidence("c1")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.recall_at_1 == 1.0
    assert result.recall_at_10 == 1.0
    assert result.reciprocal_rank == 1.0


def test_a_second_place_hit_misses_recall_at_1():
    adapter = _StubAdapter([_evidence("c1"), _evidence("c5")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.recall_at_1 == 0.0
    assert result.recall_at_5 == 1.0
    assert result.reciprocal_rank == 0.5


def test_a_miss_scores_zero_and_still_records_what_came_back():
    adapter = _StubAdapter([_evidence("c1")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.recall_at_10 == 0.0
    assert result.ranked_sources == ("c1",)
    assert result.evidence_texts == ("body of c1",)


def test_the_adapter_is_asked_for_k_hits():
    adapter = _StubAdapter([_evidence("c5")])
    run_track_r(adapter, [_question()], k=10)
    assert adapter.asked == [("por que se revirtio WAL", 10)]


def test_strata_and_timing_travel_with_the_result():
    adapter = _StubAdapter([_evidence("c5")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.strata == ("es", "no-overlap")
    assert result.seconds >= 0.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_run_track_r.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.run_track_r'`.

- [ ] **Step 3: Write the minimal implementation**

`membench/question_result.py`:

```python
"""What Track R measured for one question."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuestionResult:
    """One question's source-discovery result.

    Attributes:
        question_id: Which question this is.
        strata: The question's tags, for descriptive breakdowns only.
        ranked_sources: Conversation ids the system returned, best first.
        recall_at_1: 1.0 when the answer conversation ranked first.
        recall_at_5: 1.0 when it appeared in the first five.
        recall_at_10: 1.0 when it appeared in the first ten.
        reciprocal_rank: 1/rank of the answer conversation, 0.0 when absent.
        seconds: Wall-clock duration of this single query.
        evidence_texts: The evidence as returned, kept so a miss can be read.
    """

    question_id: str
    strata: tuple[str, ...]
    ranked_sources: tuple[str, ...]
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    reciprocal_rank: float
    seconds: float
    evidence_texts: tuple[str, ...]
```

`membench/run_track_r.py`:

```python
"""Score a memory system's source discovery over a labelled question set."""

import time
from collections.abc import Sequence

from membench.adapter import MemoryAdapter
from membench.question import Question
from membench.question_result import QuestionResult
from membench.ranked_sources import ranked_sources
from membench.recall_at_k import recall_at_k
from membench.reciprocal_rank import reciprocal_rank


def run_track_r(
    adapter: MemoryAdapter, questions: Sequence[Question], k: int = 10
) -> list[QuestionResult]:
    """Ask every question and score which conversation the system found.

    This measures source discovery, not memory quality: a system can return
    the right conversation and the superseded version of the fact, and score
    1.0 here. Track A is what catches that.

    Args:
        adapter: The system under test, already set up and ingested.
        questions: The labelled question set.
        k: How deep the ranking is requested and scored.

    Returns:
        One result per question, in question order.
    """
    results: list[QuestionResult] = []
    for question in questions:
        started = time.monotonic()
        evidence = adapter.query(question.question, k)
        seconds = time.monotonic() - started
        sources = ranked_sources(evidence)
        answer = question.answer_conversation_id
        results.append(
            QuestionResult(
                question_id=question.question_id,
                strata=question.strata,
                ranked_sources=tuple(sources),
                recall_at_1=recall_at_k(sources, answer, 1),
                recall_at_5=recall_at_k(sources, answer, 5),
                recall_at_10=recall_at_k(sources, answer, 10),
                reciprocal_rank=reciprocal_rank(sources, answer),
                seconds=seconds,
                evidence_texts=tuple(hit.text for hit in evidence),
            )
        )
    return results
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_run_track_r.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add membench/question_result.py membench/run_track_r.py tests/test_run_track_r.py
git commit -m "feat: run track R over a labelled question set"
```

---

### Task 8: The run manifest

**Files:**
- Create: `membench/sha256_file.py`
- Create: `membench/build_manifest.py`
- Test: `tests/test_sha256_file.py`
- Test: `tests/test_build_manifest.py`

**Interfaces:**
- Consumes: nothing beyond the stdlib.
- Produces: `sha256_file(path: Path) -> str`, `build_manifest(run_id: str, adapter_name: str, corpus_path: Path, questions_path: Path, k: int) -> dict[str, object]`.

The spec requires that reproducing the report exactly and rerunning inference are distinguishable. A command line does not capture which corpus bytes were read, so the manifest hashes them.

- [ ] **Step 1: Write the failing tests**

`tests/test_sha256_file.py`:

```python
from pathlib import Path

from membench.sha256_file import sha256_file


def test_hashes_the_bytes_of_the_file(tmp_path: Path):
    path = tmp_path / "a.txt"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_the_same_content_hashes_the_same(tmp_path: Path):
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_bytes(b"same")
    second.write_bytes(b"same")
    assert sha256_file(first) == sha256_file(second)
```

`tests/test_build_manifest.py`:

```python
from pathlib import Path

from membench.build_manifest import build_manifest


def test_the_manifest_pins_the_inputs(tmp_path: Path):
    corpus = tmp_path / "corpus.jsonl"
    questions = tmp_path / "questions.jsonl"
    corpus.write_bytes(b"{}")
    questions.write_bytes(b"{}")
    manifest = build_manifest(
        run_id="2026-09-17-abc",
        adapter_name="baseline_fts5",
        corpus_path=corpus,
        questions_path=questions,
        k=10,
    )
    assert manifest["run_id"] == "2026-09-17-abc"
    assert manifest["adapter"] == "baseline_fts5"
    assert manifest["k"] == 10
    assert manifest["corpus"]["path"] == str(corpus)
    assert len(manifest["corpus"]["sha256"]) == 64
    assert len(manifest["questions"]["sha256"]) == 64


def test_the_manifest_records_the_track_it_scored(tmp_path: Path):
    path = tmp_path / "f.jsonl"
    path.write_bytes(b"{}")
    manifest = build_manifest(
        run_id="r", adapter_name="a", corpus_path=path, questions_path=path, k=1
    )
    assert manifest["track"] == "R: source discovery"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_sha256_file.py tests/test_build_manifest.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.sha256_file'`.

- [ ] **Step 3: Write the minimal implementation**

`membench/sha256_file.py`:

```python
"""Hash a file's bytes, so a manifest pins content rather than a path."""

import hashlib
from pathlib import Path

_CHUNK = 1 << 20


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 of a file's bytes.

    Args:
        path: The file to hash.

    Returns:
        The 64-character hex digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()
```

`membench/build_manifest.py`:

```python
"""Describe a run precisely enough to recompute its report."""

from pathlib import Path

from membench.sha256_file import sha256_file


def build_manifest(
    run_id: str, adapter_name: str, corpus_path: Path, questions_path: Path, k: int
) -> dict[str, object]:
    """Return the manifest that pins a run's inputs.

    A command line does not say which bytes were read, so the corpus and the
    question set are hashed. Reproducing the report from frozen artifacts and
    rerunning inference are different operations, and this is what makes the
    first one checkable.

    Args:
        run_id: Identity of this run.
        adapter_name: Which system was measured.
        corpus_path: The corpus that was ingested.
        questions_path: The labelled question set that was asked.
        k: Ranking depth requested and scored.

    Returns:
        A JSON-serialisable manifest.
    """
    return {
        "run_id": run_id,
        "track": "R: source discovery",
        "adapter": adapter_name,
        "k": k,
        "corpus": {"path": str(corpus_path), "sha256": sha256_file(corpus_path)},
        "questions": {"path": str(questions_path), "sha256": sha256_file(questions_path)},
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_sha256_file.py tests/test_build_manifest.py -v`
Expected: PASS, 4 tests.

- [ ] **Step 5: Commit**

```bash
git add membench/sha256_file.py membench/build_manifest.py tests/
git commit -m "feat: hash a run's inputs into a manifest"
```

---

### Task 9: The CLI, and the first real number

**Files:**
- Create: `membench/cli.py`
- Create: `membench/write_run.py`
- Create: `README.md`
- Test: `tests/test_write_run.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything from Tasks 1–8.
- Produces: `write_run(out_dir: Path, manifest: dict[str, object], results: Sequence[QuestionResult], ingest: IngestReport) -> None`, `main(argv: Sequence[str] | None = None) -> int`.

- [ ] **Step 1: Write the failing tests**

`tests/test_write_run.py`:

```python
import json
from pathlib import Path

from membench.ingest_report import IngestReport
from membench.question_result import QuestionResult
from membench.write_run import write_run


def _result() -> QuestionResult:
    return QuestionResult(
        question_id="q1",
        strata=("es",),
        ranked_sources=("c5",),
        recall_at_1=1.0,
        recall_at_5=1.0,
        recall_at_10=1.0,
        reciprocal_rank=1.0,
        seconds=0.01,
        evidence_texts=("body",),
    )


def test_writes_the_manifest_and_one_line_per_question(tmp_path: Path):
    write_run(
        out_dir=tmp_path,
        manifest={"run_id": "r"},
        results=[_result()],
        ingest=IngestReport(seconds=1.0, index_bytes=10, input_tokens=0, output_tokens=0),
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == "r"
    assert manifest["ingest"]["index_bytes"] == 10
    lines = (tmp_path / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(lines[0])["question_id"] == "q1"
    assert json.loads(lines[0])["evidence_texts"] == ["body"]


def test_creates_the_directory_when_it_is_missing(tmp_path: Path):
    target = tmp_path / "nested" / "run"
    write_run(
        out_dir=target,
        manifest={},
        results=[],
        ingest=IngestReport(seconds=0.0, index_bytes=0, input_tokens=0, output_tokens=0),
    )
    assert (target / "raw.jsonl").exists()
```

`tests/test_cli.py`:

```python
import json
from pathlib import Path

from membench.cli import main

FIXTURE = Path(__file__).resolve().parent.parent / "corpora" / "fixture"


def test_a_baseline_run_over_the_fixture_produces_scores(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = main(
        [
            "run",
            "--adapter",
            "baseline_fts5",
            "--corpus",
            str(FIXTURE / "corpus.jsonl"),
            "--questions",
            str(FIXTURE / "questions.jsonl"),
            "--out",
            str(out),
        ]
    )
    assert exit_code == 0
    lines = (out / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6
    recalls = [json.loads(line)["recall_at_10"] for line in lines]
    assert sum(recalls) > 0


def test_an_unknown_adapter_is_refused(tmp_path: Path):
    exit_code = main(
        [
            "run",
            "--adapter",
            "nope",
            "--corpus",
            str(FIXTURE / "corpus.jsonl"),
            "--questions",
            str(FIXTURE / "questions.jsonl"),
            "--out",
            str(tmp_path / "run"),
        ]
    )
    assert exit_code == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_write_run.py tests/test_cli.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.write_run'`.

- [ ] **Step 3: Write the minimal implementation**

`membench/write_run.py`:

```python
"""Write a run's frozen artifacts to disk."""

import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from membench.ingest_report import IngestReport
from membench.question_result import QuestionResult


def write_run(
    out_dir: Path,
    manifest: dict[str, object],
    results: Sequence[QuestionResult],
    ingest: IngestReport,
) -> None:
    """Write `manifest.json` and `raw.jsonl` into the run directory.

    The raw file keeps the evidence text as returned, so a miss can be read
    rather than guessed at.

    Args:
        out_dir: Directory for this run; created if missing.
        manifest: The run manifest, extended here with the ingest cost.
        results: One entry per question.
        ingest: What ingesting the corpus cost.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    full_manifest = {**manifest, "ingest": asdict(ingest)}
    (out_dir / "manifest.json").write_text(
        json.dumps(full_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [json.dumps(asdict(result), ensure_ascii=False) for result in results]
    (out_dir / "raw.jsonl").write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")
```

`membench/cli.py`:

```python
"""Command line for running a memory system against a labelled question set."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from membench.adapters.baseline_fts5 import BaselineFts5Adapter
from membench.build_manifest import build_manifest
from membench.load_corpus import load_corpus
from membench.load_questions import load_questions
from membench.run_track_r import run_track_r
from membench.write_run import write_run

_ADAPTERS = {"baseline_fts5": BaselineFts5Adapter}


def main(argv: Sequence[str] | None = None) -> int:
    """Run one system over one corpus and write the run's artifacts.

    Args:
        argv: Command-line arguments, or None to read `sys.argv`.

    Returns:
        0 on success, 2 when the requested adapter does not exist.
    """
    parser = argparse.ArgumentParser(prog="membench")
    subcommands = parser.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run", help="Score one system's source discovery")
    run.add_argument("--adapter", required=True)
    run.add_argument("--corpus", type=Path, required=True)
    run.add_argument("--questions", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--k", type=int, default=10)
    args = parser.parse_args(argv)

    factory = _ADAPTERS.get(args.adapter)
    if factory is None:
        print(f"unknown adapter: {args.adapter}; known: {', '.join(sorted(_ADAPTERS))}")
        return 2

    adapter = factory(args.out / "index.db")
    adapter.setup()
    ingest = adapter.ingest(load_corpus(args.corpus))
    results = run_track_r(adapter, load_questions(args.questions), args.k)
    adapter.teardown()

    manifest = build_manifest(
        run_id=args.out.name,
        adapter_name=args.adapter,
        corpus_path=args.corpus,
        questions_path=args.questions,
        k=args.k,
    )
    write_run(args.out, manifest, results, ingest)
    print(f"wrote {args.out}/raw.jsonl and {args.out}/manifest.json")
    return 0
```

Note for the implementer: `adapter.setup()` writes `args.out / "index.db"`, so `write_run` must not be the first thing to create that directory. `BaselineFts5Adapter.setup` calls `sqlite3.connect`, which fails if the parent directory is missing — add `args.out.mkdir(parents=True, exist_ok=True)` immediately before `adapter.setup()` in `main`, and keep `write_run`'s own `mkdir` because `write_run` is also used on its own.

`README.md`:

```markdown
# memory-bench

A two-track benchmark for agent memory systems.

**Track R — source discovery.** Which conversation a system finds for a
question. This is not memory quality: a system can return the right
conversation and the superseded version of the fact.

**Track A — answer sufficiency.** Whether the evidence a system returns, under
a token budget identical for every system, lets one fixed reader answer the
question. Implemented in a later plan.

What no published benchmark does today, and what this one is for: a non-English
corpus, the two tracks kept apart, and operability scored with evidence.

Design: `docs/superpowers/specs/2026-09-17-memory-bench-design.md`.

## Run the baseline over the fixture corpus

```bash
uv run membench run \
  --adapter baseline_fts5 \
  --corpus corpora/fixture/corpus.jsonl \
  --questions corpora/fixture/questions.jsonl \
  --out results/fixture-baseline
```

The floor is the point: SQLite FTS5 with no model, no embedding and no
extraction. Every sophisticated system is measured by how far above it lands.
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/ -v`
Expected: PASS, all tests.

- [ ] **Step 5: Run the gate and the real command**

Run: `uv run codeality-py gate`
Expected: clean, coverage at or above 80.

Run:

```bash
uv run membench run --adapter baseline_fts5 \
  --corpus corpora/fixture/corpus.jsonl \
  --questions corpora/fixture/questions.jsonl \
  --out results/fixture-baseline
```

Expected: `wrote results/fixture-baseline/raw.jsonl and .../manifest.json`.

Then read the result and record it in the commit message — this is the first
real number the project produces:

```bash
python3 -c "
import json, pathlib
rows = [json.loads(l) for l in pathlib.Path('results/fixture-baseline/raw.jsonl').read_text().splitlines()]
n = len(rows)
for metric in ('recall_at_1', 'recall_at_5', 'recall_at_10', 'reciprocal_rank'):
    print(metric, round(sum(r[metric] for r in rows) / n, 3))
"
```

Note for the implementer: question `q3` ("en que modo esta la base de datos
ahora mismo") is expected to MISS. It shares no informative word with `c5`, and
the baseline is lexical. That miss is the point of the fixture, not a bug — do
not tune the fixture until it passes.

- [ ] **Step 6: Commit**

```bash
git add membench/cli.py membench/write_run.py README.md tests/
git commit -m "feat: membench run, scoring a system end to end over a corpus"
```

---

## What this plan deliberately does not build

Each of these is a later plan, and building it here would produce something
untestable without a VM, a gateway or a quota:

- Corpus A, its generator, the Codex critic pass and the human audit.
- The `model-gateway` and the mem0 adapter.
- The Atrium adapter, which needs `synthesize` and `ingest-synthesis` to be
  measuring anything at all.
- Track A, its token budget and its fixed reader.
- The operability capability matrix.
- `THRESHOLDS.md` and star assignment, which are derived from the baseline
  pilot this plan makes possible.
