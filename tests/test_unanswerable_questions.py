"""What a run reports for questions the corpus deliberately cannot answer."""

from membench.abstention_rate import abstention_rate
from membench.evidence import Evidence
from membench.metric_means import metric_means
from membench.question import Question
from membench.run_track_r import run_track_r


class _StubAdapter:
    def __init__(self, hits: list[Evidence]) -> None:
        self._hits = hits

    def setup(self) -> None: ...

    def ingest(self, corpus): ...

    def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
        return self._hits[:k]

    def teardown(self) -> None: ...


def _answerable(question_id: str = "q1") -> Question:
    return Question(
        question_id=question_id,
        question=question_id,
        answer_conversation_ids=("c5",),
        strata=(),
    )


def _unanswerable(question_id: str = "qx") -> Question:
    return Question(
        question_id=question_id,
        question=question_id,
        answer_conversation_ids=(),
        strata=(),
    )


def _evidence(conversation_id: str) -> Evidence:
    return Evidence(
        text=f"body of {conversation_id}",
        native_id=conversation_id,
        source_ids=(conversation_id,),
        timestamp=None,
    )


def _unsourced() -> Evidence:
    return Evidence(text="a memory I wrote myself", native_id="m1", source_ids=(), timestamp=None)


def test_an_unanswerable_question_has_no_recall_to_report():
    result = run_track_r(_StubAdapter([_evidence("c5")]), [_unanswerable()])[0]
    assert result.answerable is False
    assert result.recall_any_at_1 is None
    assert result.recall_any_at_5 is None
    assert result.recall_any_at_10 is None
    assert result.recall_all_at_1 is None
    assert result.recall_all_at_5 is None
    assert result.recall_all_at_10 is None
    assert result.reciprocal_rank is None
    assert result.abstained is False


def test_returning_nothing_to_an_unanswerable_question_is_abstaining():
    result = run_track_r(_StubAdapter([]), [_unanswerable()])[0]
    assert result.abstained is True


def test_an_answerable_question_carries_no_abstention_verdict():
    result = run_track_r(_StubAdapter([]), [_answerable()])[0]
    assert result.answerable is True
    assert result.abstained is None
    assert result.recall_any_at_1 == 0.0


def test_unsourced_evidence_on_an_unanswerable_question_is_not_abstaining():
    """Silence and unattributable text are not the same behaviour.

    A system that emits a memory naming no source has answered a question it
    should have declined. Counting that as abstention would pay it for the
    text, and the free rides this harness has already closed were all of that
    shape - a system rewarded for returning something less checkable.
    """
    result = run_track_r(_StubAdapter([_unsourced()]), [_unanswerable()])[0]
    assert result.abstained is False
    assert result.recall_any_at_1 is None


def test_an_unanswerable_question_never_false_matches_an_unsourced_slot():
    """The hazard the empty label set removed rather than guarded again.

    An unsourced rank slot is recorded as None. While the absent label was
    also None, a system returning one unattributable hit matched the one
    question that cannot be matched. The label set is empty now, so there is
    nothing left for that slot to equal, and the metrics are None for the
    honest reason: the question has no answer to find.
    """
    result = run_track_r(_StubAdapter([_unsourced(), _unsourced()]), [_unanswerable()])[0]
    assert result.ranked_sources == (None, None)
    assert result.recall_any_at_1 is None
    assert result.reciprocal_rank is None


def test_abstaining_everywhere_does_not_lift_a_single_recall():
    """The free ride this half of the task exists to close.

    A system that returns nothing on every question scores zero recall on the
    answerable questions and a perfect abstention rate on the unanswerable
    ones. Both are reported; neither is averaged into the other, so returning
    less can never raise a retrieval number. This harness has closed three
    scoring free rides already - evidence without provenance costing nothing,
    an excluded system outscoring one that earned a zero, and exclusion
    decided per response - and an unanswerable question whose empty ranking
    counted as a hit would have been the fourth.
    """
    questions = [_answerable(), _unanswerable()]
    results = run_track_r(_StubAdapter([]), questions)

    means = metric_means(results)
    assert means["recall_any_at_1"] == 0.0
    assert means["recall_all_at_1"] == 0.0
    assert means["reciprocal_rank"] == 0.0
    assert abstention_rate(results) == 1.0


def test_an_unanswerable_row_is_not_in_any_metric_denominator():
    """One hit and one unanswerable question is a recall of 1.0, not of 0.5.

    The unanswerable row must leave the denominator entirely. Scored as a miss
    it would punish a system for a question it was right to decline; averaged
    in as a hit it would pay it for declining. It is simply not a retrieval
    measurement.
    """
    results = run_track_r(_StubAdapter([_evidence("c5")]), [_answerable(), _unanswerable()])
    assert metric_means(results)["recall_any_at_1"] == 1.0


def test_abstention_is_none_when_nothing_was_unanswerable():
    results = run_track_r(_StubAdapter([]), [_answerable()])
    assert abstention_rate(results) is None


def test_abstention_counts_only_the_unanswerable_rows():
    """Silence on an answerable question buys no abstention credit.

    Two questions, one of each kind, and a system that returns nothing at all.
    Its abstention rate is 1.0 over the one unanswerable question, not 1.0
    over two - and if it had answered the unanswerable one it would be 0.0
    however silent it had been elsewhere.
    """
    silent = run_track_r(_StubAdapter([]), [_answerable(), _unanswerable()])
    assert abstention_rate(silent) == 1.0

    talkative = run_track_r(_StubAdapter([_evidence("c5")]), [_answerable(), _unanswerable()])
    assert abstention_rate(talkative) == 0.0


def test_a_half_abstaining_run_reports_the_share():
    class _PerQuestion(_StubAdapter):
        def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
            return [] if question == "qx" else [_evidence("c5")]

    results = run_track_r(_PerQuestion([]), [_unanswerable("qx"), _unanswerable("qy")])
    assert abstention_rate(results) == 0.5
