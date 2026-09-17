"""The version of the `raw.jsonl` row schema this harness writes."""

RAW_SCHEMA_VERSION = "1.0"
"""Version of one `raw.jsonl` row.

Rows travel on their own: they are concatenated across runs, loaded years
apart and re-scored by tools this repository does not own, so the version sits
on every row rather than only on the run that produced it. It is raised
whenever a field changes meaning, is removed, or becomes newly nullable; a
purely additive field raises the minor part.
"""
