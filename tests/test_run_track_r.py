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
