"""The harness's one definition of a token."""


def count_tokens(text: str) -> int:
    """Return the number of tokens in `text`.

    A token is a whitespace-separated run of characters. This is deliberately
    not a model's tokenizer: a budget has to mean the same thing for every
    system under test and for a reader checking the result years later, and no
    model's tokenizer is stable across versions or fair across languages. It
    over-counts nothing and under-counts agglutinative text equally for
    everyone, which is the property a shared budget needs.
    """
    return len(text.split())
