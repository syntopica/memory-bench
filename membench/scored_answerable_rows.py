"""The rows a Track R mean is taken over."""

from collections.abc import Sequence

from membench.question_result import QuestionResult


def scored_answerable_rows(results: Sequence[QuestionResult]) -> list[QuestionResult]:
    """Return the rows that contribute to a Track R mean.

    Two units need this population: the one that averages the metrics and the
    one that counts how many rows each average rested on. They had the filter
    written out twice, which made the claim that they cannot drift untrue - a
    change to one would have gone unnoticed, and a mean published beside a
    count taken over a different set of rows is worse than no count at all.
    One definition, imported by both.

    A row contributes when the question was answerable and the run was
    scorable. Both are decided before any system is asked: `answerable` is a
    property of the question set, identical for every system measured on it,
    and `applicability` is a verdict on the whole run that is all-or-nothing.
    So no adapter can move a row into or out of this population by changing
    what it returns, which is what keeps the counts from becoming a lever.

    Args:
        results: Every question's result, in question order.

    Returns:
        The contributing rows, in the order given.
    """
    return [result for result in results if result.answerable and result.applicability == "scored"]
