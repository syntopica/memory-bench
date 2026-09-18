"""The harness's one definition of a token."""


def count_tokens(text: str) -> int:
    """Return the number of tokens in `text`.

    A token is a whitespace-separated run of characters. This is deliberately
    not a model's tokenizer: a budget has to mean the same thing for every
    system under test and for a reader checking the result years later, and no
    model's tokenizer is stable across versions. What this definition buys is
    that every system in a run is charged identically for the same text, which
    is the property a shared budget needs.

    What it does not buy is fairness between writing systems, and the limit is
    named here rather than discovered later. The counter is only meaningful
    for whitespace-delimited scripts. Spanish and English, the two this
    benchmark measures, split identically per whitespace run. An unsegmented
    script does not: a whole Chinese or Japanese sentence costs one token, so
    a budget that binds in Spanish is effectively unbounded there. A run of
    punctuation is also billable while carrying no content. A corpus in an
    unsegmented script needs a different definition, and using this one would
    hand that system a budget nobody else got.
    """
    return len(text.split())
