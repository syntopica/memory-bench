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
    - **An empty string, anywhere.** Same gap, written differently. Collapsing
      it into "falsy means unanswerable" would take the accidental absence for
      the deliberate one, and those are the two cases this function exists to
      keep apart.
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
        ValueError: On any of the four refusals above.
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
        if not isinstance(single, str) or not single:
            msg = f"question {question_id} has an empty answer_conversation_id"
            raise ValueError(msg)
        return (single,)
    plural = record["answer_conversation_ids"]
    if not isinstance(plural, list):
        msg = f"question {question_id}: answer_conversation_ids must be a list"
        raise ValueError(msg)
    if any(not isinstance(one, str) or not one for one in plural):
        msg = (
            f"question {question_id} has an empty answer_conversation_id in answer_conversation_ids"
        )
        raise ValueError(msg)
    return tuple(plural)
