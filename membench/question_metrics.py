"""The Track R metrics for one question, or nothing where they are undefined."""

from collections.abc import Sequence

from membench.recall_all_at_k import recall_all_at_k
from membench.recall_any_at_k import recall_any_at_k
from membench.recall_at_depth import recall_at_depth
from membench.reciprocal_rank import reciprocal_rank


def question_metrics(
    ranked: Sequence[str | None], answer_ids: Sequence[str], k: int, *, scorable: bool
) -> dict[str, float | None]:
    """Return the seven scored numbers for one question, `None` where undefined.

    Two different facts make every number here `None`, and they are recorded
    separately on the result rather than collapsed into one absent cell:
    `applicability` says the system produced no provenance anywhere in the run
    and is unscorable on this track, and `answerable` says the corpus
    deliberately cannot answer this question. A reader who sees a `null` and
    cannot tell which happened cannot tell a system that failed from a question
    that had no answer.

    Neither is a zero. A zero is a claim that the system looked and missed, and
    publishing one for a question with no target would let a system with no
    targets outscore one that searched honestly.

    Args:
        ranked: The ranking already cut at `k`. A None entry is a slot an
            unsourced hit spent; it never matches.
        answer_ids: Every labelled answer conversation, empty when the corpus
            deliberately cannot answer the question.
        k: The depth the run requested and observed.
        scorable: Whether the run as a whole is applicable to Track R.

    Returns:
        One entry per metric, keyed exactly as `QuestionResult` names them.
    """
    undefined = not scorable or not answer_ids
    metrics: dict[str, float | None] = {}
    for label, recall in (("any", recall_any_at_k), ("all", recall_all_at_k)):
        for depth in (1, 5, 10):
            metrics[f"recall_{label}_at_{depth}"] = (
                None if undefined else recall_at_depth(recall, ranked, answer_ids, depth, k)
            )
    metrics["reciprocal_rank"] = None if undefined else reciprocal_rank(ranked, answer_ids)
    return metrics
