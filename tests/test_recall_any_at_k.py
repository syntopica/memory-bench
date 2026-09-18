import pytest

from membench.recall_any_at_k import recall_any_at_k


def test_hit_inside_k_scores_one():
    assert recall_any_at_k(["c1", "c2", "c3"], ("c2",), 3) == 1.0


def test_hit_outside_k_scores_zero():
    assert recall_any_at_k(["c1", "c2", "c3"], ("c3",), 2) == 0.0


def test_absent_answer_scores_zero():
    assert recall_any_at_k(["c1", "c2"], ("c9",), 10) == 0.0


def test_empty_ranking_scores_zero():
    assert recall_any_at_k([], ("c1",), 10) == 0.0


def test_one_of_several_labels_inside_k_is_enough():
    assert recall_any_at_k(["c1", "c2"], ("c9", "c2"), 10) == 1.0


def test_no_label_inside_k_scores_zero():
    assert recall_any_at_k(["c1", "c2"], ("c8", "c9"), 10) == 0.0


def test_an_unsourced_slot_never_matches():
    assert recall_any_at_k([None, None], ("c1",), 10) == 0.0


def test_k_must_be_positive():
    with pytest.raises(ValueError, match="k must be positive"):
        recall_any_at_k(["c1"], ("c1",), 0)


def test_an_empty_label_set_is_refused_rather_than_scored():
    """An unanswerable question must never reach a recall metric.

    There is no defensible number here: 0.0 would publish a miss the system
    could not have avoided, and 1.0 would hand a hit to anything at all.
    Refusing makes the caller decide, in the open, that the row is undefined.
    """
    with pytest.raises(ValueError, match="answer_ids must not be empty"):
        recall_any_at_k(["c1"], (), 10)
