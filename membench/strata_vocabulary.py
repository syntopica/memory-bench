"""The fixed set of stratum tags a question may carry, spelled out in full.

This is the spec's vocabulary, not a project convention, and it is carried
here verbatim rather than as a reference to it, so that validating a question
set never depends on a private path or a document nobody in this repository
can open. A question tags exactly one value from each of the four required
dimensions below, plus optionally the fifth: "temporal-contradiction" marks a
question whose correct answer changed over time, which is what makes an
`as_of`-dated question checkable at all.

A typo here (`"eng"` for `"en"`, `"reciente"` for `"recent"`) is silent
without a fixed list to check against: it creates a stratum of one and an
empty one beside it in every per-stratum breakdown, and nothing about a
passing run says so.
"""

STRATA_VOCABULARY: dict[str, frozenset[str]] = {
    "language": frozenset({"es", "en"}),
    "source shape": frozenset({"conversation", "note"}),
    "vocabulary overlap": frozenset({"overlap", "no-overlap"}),
    "age": frozenset({"recent", "old"}),
}

OPTIONAL_STRATUM_DIMENSION = "temporal contradiction"
OPTIONAL_STRATUM_TAGS: frozenset[str] = frozenset({"temporal-contradiction"})
