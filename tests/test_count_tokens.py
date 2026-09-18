from membench.count_tokens import count_tokens


def test_it_counts_whitespace_separated_words():
    assert count_tokens("quedo en WAL desactivado") == 4


def test_it_counts_nothing_in_an_empty_string():
    assert count_tokens("") == 0
    assert count_tokens("   \n  ") == 0


def test_punctuation_attached_to_a_word_does_not_add_a_token():
    assert count_tokens("¿por que? porque si.") == 4


def test_it_is_language_agnostic():
    """The benchmark's whole differential claim is non-English retrieval.

    A counter that splits Spanish differently from English would make an
    'identical' budget mean two different things.
    """
    assert count_tokens("la base de datos") == count_tokens("the database was here")
