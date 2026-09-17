from membench.fts5_query import fts5_query


def test_tokens_are_quoted_and_ored():
    assert fts5_query("wal reverted") == '"wal" OR "reverted"'


def test_punctuation_is_dropped():
    assert (
        fts5_query("¿por que se revirtio WAL?") == '"por" OR "que" OR "se" OR "revirtio" OR "wal"'
    )


def test_accents_are_preserved():
    assert fts5_query("configuración") == '"configuración"'


def test_embedded_quotes_cannot_escape_the_term():
    assert fts5_query('a "b" c') == '"a" OR "b" OR "c"'


def test_a_query_with_no_usable_token_matches_nothing():
    assert fts5_query("¿?") == '""'
