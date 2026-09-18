from membench.run_applicability import run_applicability


def test_a_run_with_no_questions_observed_nothing_to_exclude_it_for():
    """Degenerate, and it has no rows, so both verdicts report the same means.

    The rule is single: exclusion takes evidence that carried no source. No
    questions means no such evidence, so there is nothing to carve out.
    """
    assert run_applicability([]) == "scored"


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


def test_a_run_that_returned_nothing_at_all_is_scored_as_the_misses_it_made():
    """Searching everywhere and finding nothing is a bad system, not an unmeasurable one.

    The carve-out is architectural: it is for a system whose memories carry no
    source conversation at all. A system that returned no evidence anywhere
    never exercised that architecture - it searched and failed, every time,
    which is exactly what a zero records. Excluding it would let "I find
    nothing" read as "this track does not apply to me".
    """
    assert run_applicability([(), (), ()]) == "scored"
