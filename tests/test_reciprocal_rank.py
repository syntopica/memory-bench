import pytest

from membench.reciprocal_rank import reciprocal_rank


def test_first_position_scores_one():
    assert reciprocal_rank(["c1", "c2"], "c1") == 1.0


def test_third_position_scores_one_third():
    assert reciprocal_rank(["c1", "c2", "c3"], "c3") == pytest.approx(1 / 3)


def test_absent_answer_scores_zero():
    assert reciprocal_rank(["c1", "c2"], "c9") == 0.0


def test_empty_ranking_scores_zero():
    assert reciprocal_rank([], "c1") == 0.0
