from membench.evidence import Evidence
from membench.scoring_applicability import scoring_applicability


def _evidence(*source_ids: str) -> Evidence:
    return Evidence(text="t", native_id="e", source_ids=source_ids, timestamp=None)


def test_a_system_that_returned_nothing_is_scored_as_a_miss():
    assert scoring_applicability([], []) == "scored"


def test_a_system_that_returned_provenance_is_scored():
    assert scoring_applicability([_evidence("c1")], ["c1"]) == "scored"


def test_a_system_with_evidence_but_no_provenance_is_not_applicable():
    assert scoring_applicability([_evidence()], []) == "not_applicable"


def test_a_lone_none_slot_is_not_applicable():
    """The real shape ranked_sources produces for an unsourced hit.

    `[]` above is a defensive edge case; `[None]` is what an unsourced piece
    of evidence actually resolves to, and is the branch the guard exists for.
    """
    assert scoring_applicability([_evidence()], [None]) == "not_applicable"
