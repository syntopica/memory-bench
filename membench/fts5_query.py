"""Turn a natural-language question into a safe FTS5 MATCH expression."""

import re

_TOKEN = re.compile(r"\w+", re.UNICODE)


def fts5_query(text: str) -> str:
    """Return an FTS5 MATCH expression that ORs every word of the question.

    FTS5 MATCH takes a query language, not a sentence: a bare question mark or
    hyphen raises `sqlite3.OperationalError: fts5: syntax error`, which would
    score the baseline zero for a reason unrelated to retrieval. Each word is
    therefore quoted as a literal term, and OR keeps recall high, which is what
    a floor is for.

    Args:
        text: The question as a person asked it.

    Returns:
        A MATCH expression. A question with no word characters returns `""`,
        which is valid and matches nothing.
    """
    tokens = [token.lower() for token in _TOKEN.findall(text)]
    if not tokens:
        return '""'
    return " OR ".join(f'"{token}"' for token in tokens)
