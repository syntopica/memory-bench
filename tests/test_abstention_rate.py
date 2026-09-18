from membench.abstention_rate import abstention_rate
from membench.question_result import QuestionResult


def _result(*, answerable: bool, abstained: bool | None, applicability: str = "scored"):
    return QuestionResult(
        question_id="q1",
        strata=(),
        ranked_sources=(),
        applicability=applicability,
        answerable=answerable,
        depth=10,
        truncated=False,
        recall_any_at_1=None,
        recall_any_at_5=None,
        recall_any_at_10=None,
        recall_all_at_1=None,
        recall_all_at_5=None,
        recall_all_at_10=None,
        reciprocal_rank=None,
        abstained=abstained,
        seconds=0.0,
        evidence_texts=(),
    )


def test_a_run_with_no_unanswerable_question_observed_no_rate():
    assert abstention_rate([_result(answerable=True, abstained=None)]) is None


def test_an_empty_run_observed_no_rate():
    assert abstention_rate([]) is None


def test_it_is_the_share_of_unanswerable_rows_that_abstained():
    results = [
        _result(answerable=False, abstained=True),
        _result(answerable=False, abstained=False),
        _result(answerable=True, abstained=None),
    ]
    assert abstention_rate(results) == 0.5


def test_answerable_rows_are_not_in_the_denominator():
    """A system cannot dilute its abstention rate by staying silent elsewhere."""
    results = [_result(answerable=False, abstained=False)] + [
        _result(answerable=True, abstained=None) for _ in range(9)
    ]
    assert abstention_rate(results) == 0.0


def test_an_unscorable_run_still_reports_what_it_returned():
    """Provenance and silence are different observations.

    A system Track R cannot score - its evidence named no source anywhere -
    still either returned something or did not, and that is honestly
    observable. Reporting None here would hide a real observation behind an
    unrelated verdict.
    """
    results = [_result(answerable=False, abstained=True, applicability="not_applicable")]
    assert abstention_rate(results) == 1.0
