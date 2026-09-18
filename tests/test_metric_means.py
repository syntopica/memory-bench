from membench.metric_means import metric_means
from membench.question_result import QuestionResult


def _result(applicability: str = "scored", **overrides) -> QuestionResult:
    fields = {
        "question_id": "q1",
        "strata": ("es",),
        "ranked_sources": ("c5",),
        "applicability": applicability,
        "answerable": True,
        "depth": 10,
        "truncated": False,
        "recall_any_at_1": 1.0,
        "recall_any_at_5": 1.0,
        "recall_any_at_10": 1.0,
        "recall_all_at_1": 1.0,
        "recall_all_at_5": 1.0,
        "recall_all_at_10": 1.0,
        "reciprocal_rank": 1.0,
        "abstained": None,
        "seconds": 0.01,
        "evidence_texts": ("body",),
    }
    fields.update(overrides)
    return QuestionResult(**fields)


def _unscorable() -> QuestionResult:
    return _result(
        applicability="not_applicable",
        recall_any_at_1=None,
        recall_any_at_5=None,
        recall_any_at_10=None,
        recall_all_at_1=None,
        recall_all_at_5=None,
        recall_all_at_10=None,
        reciprocal_rank=None,
    )


def test_it_averages_the_scored_rows():
    means = metric_means([_result(), _result(recall_any_at_1=0.0, reciprocal_rank=0.5)])
    assert means["recall_any_at_1"] == 0.5
    assert means["reciprocal_rank"] == 0.75


def test_an_unscorable_row_is_excluded_rather_than_averaged_as_zero():
    means = metric_means([_result(), _unscorable()])
    assert means["recall_any_at_1"] == 1.0


def test_a_metric_no_row_observed_has_no_mean():
    means = metric_means([_result(depth=2, recall_any_at_5=None, recall_any_at_10=None)])
    assert means["recall_any_at_1"] == 1.0
    assert means["recall_any_at_5"] is None
    assert means["recall_any_at_10"] is None


def test_an_empty_run_has_no_means():
    assert metric_means([])["recall_any_at_1"] is None


def test_an_unanswerable_row_never_enters_a_mean():
    """The exclusion is pinned at this unit, not only at its caller.

    `run_track_r` already leaves every metric None on an unanswerable row, so
    a row carrying both `answerable=False` and a real number cannot arise
    today. It is constructed here anyway, because the rule this function
    publishes is "the unanswerable population is never averaged in", and a
    test that only exercises the upstream guard would pass with that rule
    deleted. The answerable row missed and the unanswerable row carries a
    1.0: the mean is the miss, not 0.5.
    """
    means = metric_means(
        [
            _result(recall_any_at_1=0.0, reciprocal_rank=0.0),
            _result(answerable=False, recall_any_at_1=1.0, reciprocal_rank=1.0),
        ]
    )
    assert means["recall_any_at_1"] == 0.0
    assert means["reciprocal_rank"] == 0.0
