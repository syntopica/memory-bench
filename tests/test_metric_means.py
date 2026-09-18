from membench.metric_means import metric_means
from membench.question_result import QuestionResult


def _result(applicability: str = "scored", **overrides) -> QuestionResult:
    fields = {
        "question_id": "q1",
        "strata": ("es",),
        "ranked_sources": ("c5",),
        "applicability": applicability,
        "depth": 10,
        "truncated": False,
        "recall_at_1": 1.0,
        "recall_at_5": 1.0,
        "recall_at_10": 1.0,
        "reciprocal_rank": 1.0,
        "seconds": 0.01,
        "evidence_texts": ("body",),
    }
    fields.update(overrides)
    return QuestionResult(**fields)


def _unscorable() -> QuestionResult:
    return _result(
        applicability="not_applicable",
        recall_at_1=None,
        recall_at_5=None,
        recall_at_10=None,
        reciprocal_rank=None,
    )


def test_it_averages_the_scored_rows():
    means = metric_means([_result(), _result(recall_at_1=0.0, reciprocal_rank=0.5)])
    assert means["recall_at_1"] == 0.5
    assert means["reciprocal_rank"] == 0.75


def test_an_unscorable_row_is_excluded_rather_than_averaged_as_zero():
    means = metric_means([_result(), _unscorable()])
    assert means["recall_at_1"] == 1.0


def test_a_metric_no_row_observed_has_no_mean():
    means = metric_means([_result(depth=2, recall_at_5=None, recall_at_10=None)])
    assert means["recall_at_1"] == 1.0
    assert means["recall_at_5"] is None
    assert means["recall_at_10"] is None


def test_an_empty_run_has_no_means():
    assert metric_means([])["recall_at_1"] is None
