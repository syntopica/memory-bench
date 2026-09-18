"""Score a memory system's source discovery over a labelled question set."""

import time
from collections.abc import Sequence

from membench.abstention_verdict import abstention_verdict
from membench.evidence import Evidence
from membench.memory_adapter import MemoryAdapter
from membench.question import Question
from membench.question_metrics import question_metrics
from membench.question_result import QuestionResult
from membench.ranked_sources import ranked_sources
from membench.run_applicability import run_applicability


def run_track_r(
    adapter: MemoryAdapter, questions: Sequence[Question], k: int = 10
) -> list[QuestionResult]:
    """Ask every question and score which conversation the system found.

    This measures source discovery, not memory quality: a system can return
    the right conversation and the superseded version of the fact, and score
    1.0 here. Track A is what catches that.

    Every question is asked before any of them is scored, because
    applicability is decided once for the whole run rather than per response.
    A system that cited a conversation on any question is scored on all of
    them; only a system whose evidence named no source on any question is
    excluded, and then entirely. Returning nothing is not that: it is a search
    that failed, and it is scored. `run_applicability` holds the reasoning.

    A question the corpus deliberately cannot answer carries an empty label
    set. Every metric is None on its row - undefined, not unobserved and not a
    miss - and what is recorded instead is whether the system abstained.
    `question_metrics` and `abstention_verdict` hold that reasoning, and
    `abstention_rate` reports the population; the two are never merged.

    Args:
        adapter: The system under test, already set up and ingested.
        questions: The labelled question set.
        k: How deep the ranking is requested and scored. It bounds the
            ranked conversations too, so one hit citing many conversations
            buys no more depth than k separate hits. Applicability is decided
            on the full rankings, before this bound is applied: a system that
            cited a real conversation past depth k still has provenance, and
            is scored a real miss rather than excluded.

    Returns:
        One result per question, in question order. Every row carries the same
        applicability verdict.
    """
    asked: list[tuple[Question, list[Evidence], tuple[str | None, ...], float]] = []
    for question in questions:
        started = time.monotonic()
        evidence = adapter.query(question.question, k, None)
        seconds = time.monotonic() - started
        asked.append((question, evidence, ranked_sources(evidence), seconds))

    applicability = run_applicability(full_sources for _, _, full_sources, _ in asked)
    scorable = applicability == "scored"

    results: list[QuestionResult] = []
    for question, evidence, full_sources, seconds in asked:
        sources = full_sources[:k]
        answer_ids = question.answer_conversation_ids
        metrics = question_metrics(sources, answer_ids, k, scorable=scorable)
        results.append(
            QuestionResult(
                question_id=question.question_id,
                strata=question.strata,
                ranked_sources=tuple(sources),
                applicability=applicability,
                answerable=bool(answer_ids),
                depth=k,
                truncated=len(full_sources) > k,
                recall_any_at_1=metrics["recall_any_at_1"],
                recall_any_at_5=metrics["recall_any_at_5"],
                recall_any_at_10=metrics["recall_any_at_10"],
                recall_all_at_1=metrics["recall_all_at_1"],
                recall_all_at_5=metrics["recall_all_at_5"],
                recall_all_at_10=metrics["recall_all_at_10"],
                reciprocal_rank=metrics["reciprocal_rank"],
                abstained=abstention_verdict(full_sources, answerable=bool(answer_ids)),
                seconds=seconds,
                evidence_texts=tuple(hit.text for hit in evidence),
            )
        )
    return results
