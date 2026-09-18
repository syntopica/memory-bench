from membench.metric_observations import metric_observations
from membench.question_result import QuestionResult


def _result(**overrides) -> QuestionResult:
    fields = {
        "question_id": "q1",
        "strata": ("en",),
        "ranked_sources": ("c1",),
        "applicability": "scored",
        "answerable": True,
        "answer_label_count": 1,
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


def test_two_means_over_different_populations_report_different_counts():
    """The reason this unit exists: side by side, undenominated means mislead.

    A question with three distinct labels observes no `recall_all_at_1` - one
    slot cannot hold three conversations - while its `recall_any_at_1` is a
    real number. Printing both as though they rested on the same questions is
    what this count prevents.
    """
    results = [
        _result(question_id="m1", answer_label_count=3, recall_all_at_1=None),
        _result(question_id="s1"),
    ]
    counts = metric_observations(results)
    assert counts["recall_any_at_1"] == 2
    assert counts["recall_all_at_1"] == 1


def test_an_unanswerable_row_is_in_no_count():
    counts = metric_observations([_result(answerable=False, answer_label_count=0)])
    assert set(counts.values()) == {0}


def test_an_unscorable_run_counts_nothing():
    counts = metric_observations([_result(applicability="not_applicable")])
    assert set(counts.values()) == {0}
