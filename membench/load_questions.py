"""Read a labelled question set from JSONL."""

import json
from pathlib import Path

from membench.question import Question


def load_questions(path: Path) -> list[Question]:
    """Return the labelled questions one JSON object per line holds.

    The keys are the ones Atrium's acceptance protocol already uses, so a
    labelled set moves between the two repositories unchanged.

    Args:
        path: The question JSONL file.

    Returns:
        The questions, in file order.

    Raises:
        ValueError: If a question carries no answer conversation, which would
            silently score as a miss for every system.
    """
    questions: list[Question] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        answer_conversation_id = record["answer_conversation_id"]
        if not answer_conversation_id:
            msg = f"question {record['question_id']} has no answer_conversation_id"
            raise ValueError(msg)
        questions.append(
            Question(
                question_id=record["question_id"],
                question=record["question"],
                answer_conversation_id=answer_conversation_id,
                strata=tuple(record["strata"]),
            )
        )
    return questions
