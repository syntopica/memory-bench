"""Read a labelled question set from JSONL."""

import json
from pathlib import Path

from membench.question import Question
from membench.validate_strata import validate_strata


def load_questions(path: Path) -> list[Question]:
    """Return the labelled questions one JSON object per line holds.

    The keys are the ones Atrium's acceptance protocol already uses, so a
    labelled set moves between the two repositories unchanged.

    A question's answer comes in three shapes, and only one of them is an
    error. A JSON `null` is the corpus stating on purpose that this question
    has no answer - the label is present and it is "none", so it is kept as
    `Question.answer_conversation_id = None` and scored as a genuine miss for
    a system that surfaces nothing. A missing key or an empty string are not
    that: both are a labelling gap, not a verdict, and loading them silently
    would score as a miss for every system regardless of what it actually
    did, which is the failure this function was written to refuse. Collapsing
    the three into "falsy means reject" would refuse the deliberate absence
    along with the accidental one, which is exactly the case this corpus adds.

    Args:
        path: The question JSONL file.

    Returns:
        The questions, in file order.

    Raises:
        ValueError: If a question has no `answer_conversation_id` key at all,
            or the key holds an empty string; or if its strata carry a tag
            outside the published vocabulary, are missing a required
            dimension, or repeat one. `validate_strata` holds that check.
    """
    questions: list[Question] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        question_id = record["question_id"]
        if "answer_conversation_id" not in record or record["answer_conversation_id"] == "":
            msg = f"question {question_id} has no answer_conversation_id"
            raise ValueError(msg)
        strata = tuple(record["strata"])
        validate_strata(question_id, strata)
        questions.append(
            Question(
                question_id=question_id,
                question=record["question"],
                answer_conversation_id=record["answer_conversation_id"],
                strata=strata,
                as_of=record.get("as_of"),
            )
        )
    return questions
