from membench.evidence import Evidence
from membench.ranked_sources import ranked_sources


def _evidence(native_id: str, *source_ids: str) -> Evidence:
    return Evidence(text="t", native_id=native_id, source_ids=source_ids, timestamp=None)


def test_returns_sources_in_rank_order():
    assert ranked_sources([_evidence("a", "c1"), _evidence("b", "c2")]) == ["c1", "c2"]


def test_deduplicates_keeping_the_best_rank():
    hits = [_evidence("a", "c1"), _evidence("b", "c1"), _evidence("c", "c2")]
    assert ranked_sources(hits) == ["c1", "c2"]


def test_normalizes_the_synthesis_namespace_before_deduplicating():
    hits = [_evidence("a", "synthesis/c1"), _evidence("b", "c1")]
    assert ranked_sources(hits) == ["c1"]


def test_one_evidence_with_several_sources_yields_each_in_order():
    assert ranked_sources([_evidence("a", "c1", "c2")]) == ["c1", "c2"]


def test_evidence_without_provenance_contributes_nothing():
    assert ranked_sources([_evidence("a")]) == []
