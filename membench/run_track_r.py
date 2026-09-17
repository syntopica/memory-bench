"""Score a memory system's source discovery over a labelled question set."""

import time
from collections.abc import Sequence

from membench.memory_adapter import MemoryAdapter
from membench.question import Question
from membench.question_result import QuestionResult
from membench.ranked_sources import ranked_sources
from membench.recall_at_depth import recall_at_depth
from membench.reciprocal_rank import reciprocal_rank
from membench.track_r_applicability import track_r_applicability


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
        applicability = track_r_applicability(evidence, sources)
        scorable = applicability == "scored"
        results.append(
            QuestionResult(
                question_id=question.question_id,
                strata=question.strata,
                ranked_sources=tuple(sources),
                applicability=applicability,
                depth=k,
                recall_at_1=recall_at_depth(sources, answer, 1, k) if scorable else None,
                recall_at_5=recall_at_depth(sources, answer, 5, k) if scorable else None,
                recall_at_10=recall_at_depth(sources, answer, 10, k) if scorable else None,
                reciprocal_rank=reciprocal_rank(sources, answer) if scorable else None,
                seconds=seconds,
                evidence_texts=tuple(hit.text for hit in evidence),
            )
        )
    return results
