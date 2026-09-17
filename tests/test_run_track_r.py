import pytest

from membench.evidence import Evidence
from membench.question import Question
from membench.run_track_r import run_track_r


class _StubAdapter:
    def __init__(self, hits: list[Evidence]) -> None:
        self._hits = hits
        self.asked: list[tuple[str, int]] = []

    def setup(self) -> None: ...

    def ingest(self, corpus): ...

    def query(self, question: str, k: int) -> list[Evidence]:
        self.asked.append((question, k))
        return self._hits[:k]

    def teardown(self) -> None: ...


def _question() -> Question:
    return Question(
        question_id="q1",
        question="por que se revirtio WAL",
        answer_conversation_id="c5",
        strata=("es", "no-overlap"),
    )


def _evidence(conversation_id: str) -> Evidence:
    return Evidence(
        text=f"body of {conversation_id}",
        native_id=conversation_id,
        source_ids=(conversation_id,),
        timestamp=None,
    )


def test_a_first_place_hit_scores_one_everywhere():
    adapter = _StubAdapter([_evidence("c5"), _evidence("c1")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.recall_at_1 == 1.0
    assert result.recall_at_10 == 1.0
    assert result.reciprocal_rank == 1.0


def test_a_second_place_hit_misses_recall_at_1():
    adapter = _StubAdapter([_evidence("c1"), _evidence("c5")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.recall_at_1 == 0.0
    assert result.recall_at_5 == 1.0
    assert result.reciprocal_rank == 0.5


def test_a_miss_scores_zero_and_still_records_what_came_back():
    adapter = _StubAdapter([_evidence("c1")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.recall_at_10 == 0.0
    assert result.ranked_sources == ("c1",)
    assert result.evidence_texts == ("body of c1",)


def test_the_adapter_is_asked_for_k_hits():
    adapter = _StubAdapter([_evidence("c5")])
    run_track_r(adapter, [_question()], k=10)
    assert adapter.asked == [("por que se revirtio WAL", 10)]


def test_strata_and_timing_travel_with_the_result():
    adapter = _StubAdapter([_evidence("c5")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.strata == ("es", "no-overlap")
    assert result.seconds >= 0.0


def test_ranked_sources_are_truncated_to_k():
    crowded = Evidence(
        text="one hit citing many conversations",
        native_id="e1",
        source_ids=("c1", "c2", "c3", "c4", "c5"),
        timestamp=None,
    )
    result = run_track_r(_StubAdapter([crowded]), [_question()], k=3)[0]
    assert result.ranked_sources == ("c1", "c2", "c3")
    assert result.recall_at_1 == 0.0


def test_a_depth_beyond_k_is_null_rather_than_a_miss():
    adapter = _StubAdapter([_evidence("c1"), _evidence("c2")])
    result = run_track_r(adapter, [_question()], k=2)[0]
    assert result.depth == 2
    assert result.recall_at_1 == 0.0
    assert result.recall_at_5 is None
    assert result.recall_at_10 is None


def test_the_default_depth_is_ten_and_scores_every_column():
    adapter = _StubAdapter([_evidence("c5")])
    result = run_track_r(adapter, [_question()])[0]
    assert result.depth == 10
    assert result.recall_at_1 == 1.0
    assert result.recall_at_5 == 1.0
    assert result.recall_at_10 == 1.0


def _no_provenance() -> Evidence:
    return Evidence(text="a memory I wrote myself", native_id="m1", source_ids=(), timestamp=None)


def test_a_system_that_returned_nothing_is_a_scored_miss():
    result = run_track_r(_StubAdapter([]), [_question()])[0]
    assert result.applicability == "scored"
    assert result.recall_at_1 == 0.0
    assert result.reciprocal_rank == 0.0


def test_a_system_with_provenance_is_scored():
    result = run_track_r(_StubAdapter([_evidence("c5")]), [_question()])[0]
    assert result.applicability == "scored"
    assert result.recall_at_1 == 1.0


def test_a_system_without_provenance_is_not_applicable_rather_than_wrong():
    result = run_track_r(_StubAdapter([_no_provenance()]), [_question()])[0]
    assert result.applicability == "not_applicable"
    assert result.recall_at_1 is None
    assert result.recall_at_5 is None
    assert result.recall_at_10 is None
    assert result.reciprocal_rank is None
    assert result.evidence_texts == ("a memory I wrote myself",)


def test_unsourced_hits_above_the_answer_cost_the_system_its_rank():
    """The scoring decision of this task, stated as a test.

    Two systems return the answer as their third piece of evidence. One cites
    wrong conversations first, the other cites nothing first. They must score
    the same: k is a budget, and both spent two slots before the answer.
    """
    wrong_first = _StubAdapter(
        [
            Evidence(text="wrong", native_id="e1", source_ids=("c9",), timestamp=None),
            Evidence(text="also wrong", native_id="e2", source_ids=("c8",), timestamp=None),
            Evidence(text="the answer", native_id="e3", source_ids=("c1",), timestamp=None),
        ]
    )
    unsourced_first = _StubAdapter(
        [
            Evidence(text="no provenance", native_id="e1", source_ids=(), timestamp=None),
            Evidence(text="no provenance either", native_id="e2", source_ids=(), timestamp=None),
            Evidence(text="the answer", native_id="e3", source_ids=("c1",), timestamp=None),
        ]
    )
    question = Question(question_id="q1", question="?", answer_conversation_id="c1", strata=())

    wrong = run_track_r(wrong_first, [question], 10)[0]
    unsourced = run_track_r(unsourced_first, [question], 10)[0]

    assert wrong.reciprocal_rank == unsourced.reciprocal_rank
    assert unsourced.reciprocal_rank == pytest.approx(1 / 3)
    assert unsourced.applicability == "scored"
