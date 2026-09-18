from membench.run_applicability import run_applicability


def test_a_run_with_no_questions_has_no_provenance():
    assert run_applicability([]) == "not_applicable"


def test_a_run_that_never_cited_a_conversation_is_not_applicable():
    assert run_applicability([(None,), (), (None, None)]) == "not_applicable"


def test_one_cited_conversation_anywhere_scores_the_whole_run():
    assert run_applicability([(None,), ("c1",), ()]) == "scored"


def test_the_verdict_does_not_depend_on_which_question_carried_the_source():
    """The exploit this unit exists to close, at its smallest.

    The same run with the sourced question last must reach the same verdict
    as with it first: applicability is read over the whole run, so a system
    cannot strip provenance from the questions it expects to lose and have
    those rows dropped from the denominator.
    """
    assert run_applicability([("c1",), (None,)]) == run_applicability([(None,), ("c1",)])
