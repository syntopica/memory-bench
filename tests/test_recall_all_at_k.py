import pytest

from membench.recall_all_at_k import recall_all_at_k


def test_the_single_label_case_matches_recall_any():
    assert recall_all_at_k(["c1", "c2"], ("c2",), 10) == 1.0
    assert recall_all_at_k(["c1", "c2"], ("c9",), 10) == 0.0


def test_every_label_inside_k_scores_one():
    assert recall_all_at_k(["c1", "c2", "c3"], ("c1", "c3"), 3) == 1.0


def test_one_label_outside_k_scores_zero():
    """Where `any` and `all` part company.

    `c1` is first and `c3` is third. At k=2 the system found one of the two
    conversations the question needs, which is a hit for `any` and a miss for
    `all`; reporting either one alone would describe a multi-hop question as
    answered or as failed when it was neither.
    """
    assert recall_all_at_k(["c1", "c2", "c3"], ("c1", "c3"), 2) == 0.0


def test_a_label_absent_from_the_ranking_scores_zero():
    assert recall_all_at_k(["c1", "c2"], ("c1", "c9"), 10) == 0.0


def test_empty_ranking_scores_zero():
    assert recall_all_at_k([], ("c1", "c2"), 10) == 0.0


def test_k_must_be_positive():
    with pytest.raises(ValueError, match="k must be positive"):
        recall_all_at_k(["c1"], ("c1",), 0)


def test_an_empty_label_set_is_refused_rather_than_scored_a_hit():
    """The free ride an empty label set would otherwise buy.

    `all(... for id in ())` is True, so an unanswerable question reaching this
    function would score a perfect 1.0 no matter what came back - a system
    returning nothing would be rewarded for it. The guard is the reason this
    cannot happen even if a future caller forgets the `answerable` check.
    """
    with pytest.raises(ValueError, match="answer_ids must not be empty"):
        recall_all_at_k([], (), 10)
