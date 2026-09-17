"""Score a memory system's source discovery over a labelled question set."""

import time
from collections.abc import Sequence

from membench.memory_adapter import MemoryAdapter
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
        k: How deep the ranking is requested and scored. It bounds the
            ranked conversations too, so one hit citing many conversations
            buys no more depth than k separate hits.

    Returns:
        One result per question, in question order.
    """
    results: list[QuestionResult] = []
    for question in questions:
        started = time.monotonic()
        evidence = adapter.query(question.question, k)
        seconds = time.monotonic() - started
        sources = ranked_sources(evidence)[:k]
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
