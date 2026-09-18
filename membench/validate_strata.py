"""Reject a question's strata before a typo becomes a silent, empty cell."""

from membench.strata_vocabulary import OPTIONAL_STRATUM_TAGS, STRATA_VOCABULARY


def validate_strata(question_id: str, strata: tuple[str, ...]) -> None:
    """Check one question's stratum tags against the spec's fixed vocabulary.

    A per-stratum breakdown groups questions by the tag they carry in each
    dimension, so a tag outside the published vocabulary - a typo, a
    forgotten rename, a value borrowed from a different corpus - does not
    fail loudly. It creates a stratum of one next to an empty one where the
    intended tag should have landed, and a passing run says nothing about it.
    This function is the one place that stands between a question record and
    that silent split: every dimension is checked exactly once, before the
    question is scored anywhere.

    Args:
        question_id: The question this validates, named in every message so
            a failure in a corpus of thousands still points at one line.
        strata: The tags this question carries, in file order.

    Raises:
        ValueError: If a tag is outside the vocabulary; if a required
            dimension (language, source shape, vocabulary overlap, age)
            carries zero or more than one tag; or if the optional
            temporal-contradiction dimension carries more than one.
    """
    known_tags = OPTIONAL_STRATUM_TAGS.union(*STRATA_VOCABULARY.values())
    for tag in strata:
        if tag not in known_tags:
            msg = f"question {question_id} has an unknown stratum tag: {tag!r}"
            raise ValueError(msg)

    for dimension, tags in STRATA_VOCABULARY.items():
        matches = [tag for tag in strata if tag in tags]
        if len(matches) == 0:
            msg = f"question {question_id} is missing a {dimension} stratum tag"
            raise ValueError(msg)
        if len(matches) > 1:
            msg = (
                f"question {question_id} carries more than one {dimension} stratum tag: {matches!r}"
            )
            raise ValueError(msg)

    optional_matches = [tag for tag in strata if tag in OPTIONAL_STRATUM_TAGS]
    if len(optional_matches) > 1:
        msg = (
            f"question {question_id} carries more than one temporal-contradiction "
            f"stratum tag: {optional_matches!r}"
        )
        raise ValueError(msg)
