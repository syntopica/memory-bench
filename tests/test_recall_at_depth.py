import pytest

from membench.recall_all_at_k import recall_all_at_k
from membench.recall_any_at_k import recall_any_at_k
from membench.recall_at_depth import recall_at_depth


def test_a_depth_within_k_is_observed():
    assert recall_at_depth(recall_any_at_k, ["c1", "c5"], ("c5",), depth=5, k=10) == 1.0
    assert recall_at_depth(recall_any_at_k, ["c1", "c5"], ("c9",), depth=5, k=10) == 0.0


def test_a_depth_deeper_than_k_is_unknown_not_zero():
    assert recall_at_depth(recall_any_at_k, ["c1", "c5"], ("c9",), depth=10, k=2) is None


def test_a_depth_equal_to_k_is_observed():
    assert recall_at_depth(recall_any_at_k, ["c1", "c5"], ("c5",), depth=2, k=2) == 1.0


def test_it_guards_whichever_recall_it_is_given():
    assert recall_at_depth(recall_all_at_k, ["c1", "c5"], ("c1", "c5"), depth=2, k=2) == 1.0
    assert recall_at_depth(recall_all_at_k, ["c1", "c5"], ("c1", "c5"), depth=10, k=2) is None


def test_a_non_positive_k_is_refused():
    with pytest.raises(ValueError):
        recall_at_depth(recall_any_at_k, ["c1"], ("c1",), depth=1, k=0)
