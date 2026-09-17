from membench.normalize_source_id import normalize_source_id


def test_strips_the_atrium_synthesis_namespace():
    assert normalize_source_id("synthesis/abc123") == "abc123"


def test_leaves_a_plain_id_alone():
    assert normalize_source_id("abc123") == "abc123"


def test_strips_only_the_leading_namespace():
    assert normalize_source_id("synthesis/synthesis/abc") == "synthesis/abc"


def test_unknown_namespace_is_left_intact():
    assert normalize_source_id("notes/abc123") == "notes/abc123"
