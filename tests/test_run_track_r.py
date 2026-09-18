import pytest

from membench.evidence import Evidence
from membench.metric_means import metric_means
from membench.question import Question
from membench.run_track_r import run_track_r


class _StubAdapter:
    def __init__(self, hits: list[Evidence]) -> None:
        self._hits = hits
        self.asked: list[tuple[str, int]] = []

    def setup(self) -> None: ...

    def ingest(self, corpus): ...

    def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
        self.asked.append((question, k))
        return self._hits[:k]

    def teardown(self) -> None: ...


class _OverflowingAdapter(_StubAdapter):
    """A stub that returns every hit it holds, ignoring k.

    A real system is expected to honor the requested depth, but run_track_r's
    own handling of provenance beyond that depth must not depend on the
    adapter also honoring it: this isolates the internal ranking-versus-
    scoring distinction from the adapter's own truncation behavior.
    """

    def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
        self.asked.append((question, k))
        return self._hits


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


def test_a_run_that_returned_nothing_at_all_is_scored_the_misses_it_made():
    """A system that finds nothing is bad, not unmeasurable.

    The carve-out is for memories that carry no source conversation, and it
    takes evidence to exercise. A system that returned nothing on every
    question never produced such a memory - it searched and failed, every
    time, which is the zero this records. Excluding it would let "I find
    nothing" read as "this track does not apply to me".
    """
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


def test_provenance_past_the_requested_depth_still_scores_the_system():
    """Applicability is a property of the system, not of k.

    Two unsourced hits followed by a hit that does carry the answer, scored
    at k=2: the answer sits past the requested depth, so it is a real miss,
    not an absence of provenance. Excluding it as not_applicable would reward
    padding a small budget with unsourced material, the same incentive this
    task closed at k=10.
    """
    adapter = _OverflowingAdapter(
        [
            Evidence(text="no provenance", native_id="e1", source_ids=(), timestamp=None),
            Evidence(text="no provenance either", native_id="e2", source_ids=(), timestamp=None),
            Evidence(text="the answer", native_id="e3", source_ids=("c1",), timestamp=None),
        ]
    )
    question = Question(question_id="q1", question="?", answer_conversation_id="c1", strata=())

    result = run_track_r(adapter, [question], k=2)[0]

    assert result.applicability == "scored"
    assert result.recall_at_1 == 0.0
    assert result.reciprocal_rank == 0.0
    assert result.ranked_sources == (None, None)


def test_a_cut_ranking_says_it_was_cut():
    adapter = _StubAdapter(
        [
            Evidence(
                text="crowded",
                native_id="e1",
                source_ids=("c1", "c2", "c3", "c4"),
                timestamp=None,
            )
        ]
    )
    question = Question(question_id="q1", question="?", answer_conversation_id="c1", strata=())

    result = run_track_r(adapter, [question], 2)[0]

    assert result.ranked_sources == ("c1", "c2")
    assert result.truncated is True


def test_a_ranking_that_fits_says_it_was_not_cut():
    adapter = _StubAdapter(
        [Evidence(text="one", native_id="e1", source_ids=("c1",), timestamp=None)]
    )
    question = Question(question_id="q1", question="?", answer_conversation_id="c1", strata=())

    result = run_track_r(adapter, [question], 10)[0]

    assert result.truncated is False


class _PerQuestionAdapter(_StubAdapter):
    """A stub whose answer depends on which question it was asked."""

    def __init__(self, hits_by_question: dict[str, list[Evidence]]) -> None:
        super().__init__([])
        self._hits_by_question = hits_by_question

    def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
        self.asked.append((question, k))
        return self._hits_by_question[question][:k]


def _labelled(question_id: str, answer: str) -> Question:
    return Question(
        question_id=question_id,
        question=question_id,
        answer_conversation_id=answer,
        strata=(),
    )


def test_an_unsourced_answer_scores_zero_when_the_run_has_provenance():
    adapter = _PerQuestionAdapter(
        {"q1": [_evidence("c1")], "q2": [_no_provenance()]},
    )
    results = run_track_r(adapter, [_labelled("q1", "c1"), _labelled("q2", "c2")])

    assert [result.applicability for result in results] == ["scored", "scored"]
    assert results[1].recall_at_1 == 0.0
    assert results[1].recall_at_5 == 0.0
    assert results[1].recall_at_10 == 0.0
    assert results[1].reciprocal_rank == 0.0


def test_a_run_without_any_provenance_is_not_applicable_on_every_row():
    adapter = _PerQuestionAdapter(
        {"q1": [_no_provenance()], "q2": []},
    )
    results = run_track_r(adapter, [_labelled("q1", "c1"), _labelled("q2", "c2")])

    assert [result.applicability for result in results] == ["not_applicable", "not_applicable"]
    assert metric_means(results) == {
        "recall_at_1": None,
        "recall_at_5": None,
        "recall_at_10": None,
        "reciprocal_rank": None,
    }


def test_stripping_provenance_on_the_questions_it_loses_buys_a_system_nothing():
    """The exploit this fix closes, stated as a test.

    Two systems retrieve identically on the two questions they can answer and
    fail identically on the three they cannot. The honest one reports the
    wrong conversations it found; the other returns the same text with the
    source ids stripped. When applicability was decided per question, the
    second system's three failures left the denominator and every headline
    metric rose from 0.4 to 1.0 on identical retrieval. Applicability is a
    property of the run, so both must now report the same means.
    """
    questions = [_labelled(f"q{index}", f"c{index}") for index in range(1, 6)]
    wins = {"q1": [_evidence("c1")], "q2": [_evidence("c2")]}
    losses = {f"q{index}": [_evidence("c9")] for index in range(3, 6)}
    stripped = {
        question_id: [
            Evidence(text=hit.text, native_id=hit.native_id, source_ids=(), timestamp=None)
            for hit in hits
        ]
        for question_id, hits in losses.items()
    }

    honest = run_track_r(_PerQuestionAdapter(wins | losses), questions)
    exploiting = run_track_r(_PerQuestionAdapter(wins | stripped), questions)

    assert metric_means(honest) == metric_means(exploiting)
    assert metric_means(exploiting)["recall_at_1"] == pytest.approx(0.4)
    assert all(result.applicability == "scored" for result in exploiting)


def test_abstaining_and_returning_unsourced_junk_score_the_same():
    sourced = {"q1": [_evidence("c1")]}
    silent = run_track_r(
        _PerQuestionAdapter(sourced | {"q2": []}),
        [_labelled("q1", "c1"), _labelled("q2", "c2")],
    )
    junk = run_track_r(
        _PerQuestionAdapter(sourced | {"q2": [_no_provenance()]}),
        [_labelled("q1", "c1"), _labelled("q2", "c2")],
    )

    assert metric_means(silent) == metric_means(junk)
    assert silent[1].applicability == junk[1].applicability == "scored"
    assert silent[1].reciprocal_rank == junk[1].reciprocal_rank == 0.0


def test_an_unanswerable_question_scores_no_metric_and_never_false_matches():
    """The guard this pins is one line and it protects the whole question class.

    `recall_at_k` asks `answer_id in ranked[:k]`, and an unsourced rank slot is
    None. A question the corpus cannot answer carries a None answer, so without
    the guard a system that returned one unsourced hit would score a hit on the
    one question that cannot be hit. Line coverage does not see this: the guard
    is a ternary, and either branch satisfies it.
    """
    question = Question(
        question_id="qx",
        question="algo que el corpus no responde",
        answer_conversation_id=None,
        strata=("es", "conversation", "no-overlap", "recent"),
    )
    result = run_track_r(_StubAdapter([_no_provenance()]), [question])[0]
    assert result.recall_at_1 is None
    assert result.recall_at_5 is None
    assert result.recall_at_10 is None
    assert result.reciprocal_rank is None
