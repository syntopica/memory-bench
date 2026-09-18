from membench.abstention_verdict import abstention_verdict


def test_an_answerable_question_has_no_verdict():
    assert abstention_verdict((), answerable=True) is None
    assert abstention_verdict(("c1",), answerable=True) is None


def test_nothing_returned_is_abstaining():
    assert abstention_verdict((), answerable=False) is True


def test_something_returned_is_not_abstaining():
    assert abstention_verdict(("c1",), answerable=False) is False


def test_an_unsourced_slot_still_counts_as_having_answered():
    assert abstention_verdict((None,), answerable=False) is False
