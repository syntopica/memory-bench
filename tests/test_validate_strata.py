import pytest

from membench.validate_strata import validate_strata


def test_a_complete_tag_set_is_accepted():
    validate_strata("q1", ("es", "conversation", "overlap", "old"))


def test_the_temporal_contradiction_tag_is_optional():
    validate_strata("q1", ("en", "note", "no-overlap", "recent", "temporal-contradiction"))


def test_an_unknown_tag_is_rejected():
    with pytest.raises(ValueError, match="reciente"):
        validate_strata("q1", ("es", "conversation", "overlap", "reciente"))


def test_two_tags_from_one_dimension_are_rejected():
    with pytest.raises(ValueError, match="language"):
        validate_strata("q1", ("es", "en", "conversation", "overlap", "old"))


def test_a_missing_dimension_is_rejected():
    with pytest.raises(ValueError, match="age"):
        validate_strata("q1", ("es", "conversation", "overlap"))
