import pytest

from membench.reciprocal_rank import reciprocal_rank


def test_first_position_scores_one():
    assert reciprocal_rank(["c1", "c2"], ("c1",)) == 1.0


def test_third_position_scores_one_third():
    assert reciprocal_rank(["c1", "c2", "c3"], ("c3",)) == pytest.approx(1 / 3)


def test_absent_answer_scores_zero():
    assert reciprocal_rank(["c1", "c2"], ("c9",)) == 0.0


def test_empty_ranking_scores_zero():
    assert reciprocal_rank([], ("c1",)) == 0.0


def test_the_best_ranked_label_is_the_one_measured():
    """The published rule, pinned so it cannot drift silently.

    Two labels, one at rank 1 and one at rank 3. The best-ranked one is
    scored, so this is 1.0; the worst-ranked convention would report 1/3.
    Both are defensible measurements and they are not the same measurement,
    so the choice is a published one rather than an implementation detail.
    """
    assert reciprocal_rank(["c1", "c2", "c3"], ("c3", "c1")) == 1.0


def test_label_order_does_not_change_the_score():
    assert reciprocal_rank(["c1", "c2", "c3"], ("c1", "c3")) == reciprocal_rank(
        ["c1", "c2", "c3"], ("c3", "c1")
    )


def test_an_unsourced_slot_never_matches():
    assert reciprocal_rank([None, "c1"], ("c1",)) == 0.5


def test_an_empty_label_set_is_refused_rather_than_scored_a_miss():
    with pytest.raises(ValueError, match="answer_ids must not be empty"):
        reciprocal_rank(["c1"], ())
