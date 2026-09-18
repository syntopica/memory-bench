"""Read a labelled question set from JSONL."""

import json
from pathlib import Path

from membench.question import Question
from membench.read_answer_labels import read_answer_labels
from membench.validate_strata import validate_strata


def load_questions(path: Path) -> list[Question]:
    """Return the labelled questions one JSON object per line holds.

    The keys are the ones Atrium's acceptance protocol already uses, so a
    labelled set moves between the two repositories unchanged, and both the
    singular and the plural spelling of the answer label are accepted -
    `read_answer_labels` holds the reasoning and every refusal.

    Args:
        path: The question JSONL file.

    Returns:
        The questions, in file order.

    Raises:
        ValueError: If a question's answer label is missing, blank, doubly
            spelled or malformed - `read_answer_labels` holds that check - or
            if its strata carry a tag outside the published vocabulary, are
            missing a required dimension, or repeat one - `validate_strata`
            holds that one.
    """
    questions: list[Question] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        question_id = record["question_id"]
        answer_conversation_ids = read_answer_labels(question_id, record)
        strata = tuple(record["strata"])
        validate_strata(question_id, strata)
        questions.append(
            Question(
                question_id=question_id,
                question=record["question"],
                answer_conversation_ids=answer_conversation_ids,
                strata=strata,
                as_of=record.get("as_of"),
            )
        )
    return questions
