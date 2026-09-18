"""Read a question record's answer labels, in either published key shape."""

from typing import Any


def read_answer_labels(question_id: str, record: dict[str, Any]) -> tuple[str, ...]:
    """Return the conversations a question record labels as answering it.

    Two key shapes are accepted because two corpora are written against this
    harness and neither should have to be rewritten to load. The singular key
    carries one id or a JSON `null`; the plural key carries a list, possibly
    empty. Both mean the same thing once read, and both collapse the deliberate
    absence onto one representation - the empty tuple - so nothing downstream
    has to know which shape the file used.

    What is refused, and why each refusal is not pedantry:

    - **Both keys at once.** There is no way to know which one the labeller
      meant, and picking one would silently score a question against a label
      its author may have replaced. A corpus is edited by hand; a half-finished
      rename is exactly how this happens.
    - **Neither key.** An absent label is a labelling gap, not a verdict. Left
      to load it would score as a miss for every system regardless of what each
      one returned, which is the failure this whole check was written against.
    - **An empty string, anywhere - including one that is only whitespace.**
      Same gap, written differently. Collapsing it into "falsy means
      unanswerable" would take the accidental absence for the deliberate one,
      and those are the two cases this function exists to keep apart. A
      whitespace-only id is not falsy, and ids are matched verbatim against
      what a system returns, so `"  "` would load and then score a miss for
      every system regardless of what any of them did - the failure this check
      exists against, arriving through the one spelling the check did not
      cover.
    - **A label that is not a string.** `7` is neither a gap nor an id, and
      reporting it as an *empty* id sends a corpus author looking for a blank
      field that is not there. Both key shapes say what is wrong with the
      value they were given.
    - **A plural key that is not a list.** `"c1"` as a string is iterable, so
      accepting it silently would label the question with three ids named
      `"c"`, `"1"` and nothing at all.

    Args:
        question_id: The record's id, named in every message so a corpus of
            thousands says which line is wrong.
        record: One decoded JSON question record.

    Returns:
        The labelled conversation ids in file order, empty for a question the
        corpus deliberately cannot answer.

    Raises:
        ValueError: On any of the five refusals above.
    """
    has_singular = "answer_conversation_id" in record
    has_plural = "answer_conversation_ids" in record
    if has_singular and has_plural:
        msg = f"question {question_id} carries both answer_conversation_id and answer_conversation_ids"
        raise ValueError(msg)
    if not has_singular and not has_plural:
        msg = f"question {question_id} has no answer_conversation_id"
        raise ValueError(msg)
    if has_singular:
        single = record["answer_conversation_id"]
        if single is None:
            return ()
        if not isinstance(single, str):
            msg = f"question {question_id}: answer_conversation_id must be a string"
            raise ValueError(msg)
        if not single.strip():
            msg = f"question {question_id} has an empty answer_conversation_id"
            raise ValueError(msg)
        return (single,)
    plural = record["answer_conversation_ids"]
    if not isinstance(plural, list):
        msg = f"question {question_id}: answer_conversation_ids must be a list"
        raise ValueError(msg)
    if any(not isinstance(one, str) for one in plural):
        msg = f"question {question_id}: every answer_conversation_ids entry must be a string"
        raise ValueError(msg)
    if any(not one.strip() for one in plural):
        msg = (
            f"question {question_id} has an empty answer_conversation_id in answer_conversation_ids"
        )
        raise ValueError(msg)
    return tuple(plural)
