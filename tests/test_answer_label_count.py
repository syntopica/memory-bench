"""What a row must carry for an empty all-recall cell to be readable."""

from membench.question import Question
from membench.run_track_r import run_track_r
from tests.test_run_track_r import _evidence, _StubAdapter


def test_the_row_carries_what_it_needs_to_read_an_empty_all_recall():
    """Two different reasons produce the same empty cell, so the row must separate them.

    `recall_all_at_5` is null when the run never looked five deep, and also
    when the question carries more than five labels - no depth of five can
    hold six conversations. `depth` answers only the first. Without the label
    count a consumer meets one null and cannot tell a shallow run from a
    question that outran the depth, which is the ambiguity this field exists
    to remove before a corpus that triggers it arrives.
    """
    question = Question(
        question_id="qm",
        question="multi",
        answer_conversation_ids=("c1", "c5"),
        strata=("en", "conversation", "overlap", "old"),
    )
    result = run_track_r(_StubAdapter([_evidence("c1")]), [question])[0]
    assert result.answer_label_count == 2
    assert result.depth == 10


def test_the_label_count_is_distinct_labels_and_matches_what_the_metric_applied():
    """The count has to be the one the metric decided on, or it promises a null it does not carry.

    `recall_all_at_k` is satisfied when every DISTINCT label is within the
    depth, so a question naming the same conversation six times needs one
    slot. If this field counted the repeats it would say six, a consumer would
    apply the published rule and expect an empty cell at depth five, and the
    row would carry 1.0 instead. Two rows with the same count and the same
    depth would then differ in nullity, which is the one thing the field was
    added to prevent.
    """
    repeated = Question(
        question_id="qr",
        question="repeated",
        answer_conversation_ids=("c1",) * 6,
        strata=("en", "conversation", "overlap", "old"),
    )
    result = run_track_r(_StubAdapter([_evidence("c1")]), [repeated])[0]
    assert result.answer_label_count == 1
    assert result.recall_all_at_5 == 1.0


def test_a_question_outrunning_the_depth_carries_the_count_that_explains_its_null():
    """The ambiguous case the field exists for, which its first test never built.

    Six distinct labels cannot fit five slots, so `recall_all_at_5` is null
    while the run looked ten deep. A consumer reading that null needs both
    numbers to conclude which of the two causes applied.
    """
    wide = Question(
        question_id="qw",
        question="wide",
        answer_conversation_ids=tuple(f"c{n}" for n in range(1, 7)),
        strata=("en", "conversation", "overlap", "old"),
    )
    result = run_track_r(_StubAdapter([_evidence("c1")]), [wide])[0]
    assert result.answer_label_count == 6
    assert result.depth == 10
    assert result.recall_all_at_5 is None
    assert result.recall_all_at_10 == 0.0
