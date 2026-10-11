"""The revision of the normative specification this harness implements."""

SPEC_REVISION = 1
"""Which revision of `docs/spec/revision-1.md` and its successors governs a run.

A result cites the specification by this number, so it is written into every
manifest. It is an integer that only ever increases: a revision is a new file
beside the old one, and an old revision is never edited after it is cited.
It moves whenever a normative rule changes - a rule added, removed or given a
different meaning - and is independent of the three artifact versions, which
date shapes rather than rules.
"""
