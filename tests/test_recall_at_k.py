import pytest

from membench.recall_at_k import recall_at_k


def test_hit_inside_k_scores_one():
    assert recall_at_k(["c1", "c2", "c3"], "c2", 3) == 1.0


def test_hit_outside_k_scores_zero():
    assert recall_at_k(["c1", "c2", "c3"], "c3", 2) == 0.0


def test_absent_answer_scores_zero():
    assert recall_at_k(["c1", "c2"], "c9", 10) == 0.0


def test_empty_ranking_scores_zero():
    assert recall_at_k([], "c1", 10) == 0.0


def test_k_must_be_positive():
    with pytest.raises(ValueError, match="k must be positive"):
        recall_at_k(["c1"], "c1", 0)
