from membench.evidence import Evidence
from membench.track_r_applicability import track_r_applicability


def _evidence(*source_ids: str) -> Evidence:
    return Evidence(text="t", native_id="e", source_ids=source_ids, timestamp=None)


def test_a_system_that_returned_nothing_is_scored_as_a_miss():
    assert track_r_applicability([], []) == "scored"


def test_a_system_that_returned_provenance_is_scored():
    assert track_r_applicability([_evidence("c1")], ["c1"]) == "scored"


def test_a_system_with_evidence_but_no_provenance_is_not_applicable():
    assert track_r_applicability([_evidence()], []) == "not_applicable"
