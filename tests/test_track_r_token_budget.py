from membench.evidence import Evidence
from membench.question import Question
from membench.run_track_r import run_track_r


class _BudgetRecordingAdapter:
    def __init__(self) -> None:
        self.budgets: list[int | None] = []

    def setup(self) -> None: ...

    def ingest(self, corpus): ...

    def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
        self.budgets.append(token_budget)
        return []

    def teardown(self) -> None: ...


def test_track_r_asks_with_an_unbounded_budget():
    adapter = _BudgetRecordingAdapter()
    question = Question(
        question_id="q1",
        question="por que se revirtio WAL",
        answer_conversation_ids=("c5",),
        strata=("es", "no-overlap"),
    )

    run_track_r(adapter, [question, question], k=3)

    assert adapter.budgets == [None, None]
