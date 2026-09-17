from membench.evidence import Evidence
from membench.ranked_sources import ranked_sources


def _evidence(native_id: str, *source_ids: str) -> Evidence:
    return Evidence(text="t", native_id=native_id, source_ids=source_ids, timestamp=None)


def test_returns_sources_in_rank_order():
    assert ranked_sources([_evidence("a", "c1"), _evidence("b", "c2")]) == ("c1", "c2")


def test_deduplicates_keeping_the_best_rank():
    hits = [_evidence("a", "c1"), _evidence("b", "c1"), _evidence("c", "c2")]
    assert ranked_sources(hits) == ("c1", "c2")


def test_normalizes_the_synthesis_namespace_before_deduplicating():
    hits = [_evidence("a", "synthesis/c1"), _evidence("b", "c1")]
    assert ranked_sources(hits) == ("c1",)


def test_one_evidence_with_several_sources_yields_each_in_order():
    assert ranked_sources([_evidence("a", "c1", "c2")]) == ("c1", "c2")


def test_an_unsourced_hit_occupies_its_slot():
    evidence = [
        Evidence(text="no provenance", native_id="a", source_ids=(), timestamp=None),
        Evidence(text="no provenance either", native_id="b", source_ids=(), timestamp=None),
        Evidence(text="the answer", native_id="c", source_ids=("c1",), timestamp=None),
    ]
    assert ranked_sources(evidence) == (None, None, "c1")


def test_two_unsourced_hits_are_not_deduplicated_into_one_slot():
    evidence = [
        Evidence(text="a", native_id="a", source_ids=(), timestamp=None),
        Evidence(text="b", native_id="b", source_ids=(), timestamp=None),
    ]
    assert ranked_sources(evidence) == (None, None)


def test_sources_inside_one_evidence_still_occupy_consecutive_slots():
    evidence = [
        Evidence(text="crowded", native_id="a", source_ids=("c1", "c2", "c3"), timestamp=None)
    ]
    assert ranked_sources(evidence) == ("c1", "c2", "c3")


def test_a_repeated_source_keeps_its_best_slot_only():
    evidence = [
        Evidence(text="first", native_id="a", source_ids=("c1",), timestamp=None),
        Evidence(text="again", native_id="b", source_ids=("c1", "c2"), timestamp=None),
    ]
    assert ranked_sources(evidence) == ("c1", "c2")
