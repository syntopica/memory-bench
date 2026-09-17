# memory-bench

A two-track benchmark for agent memory systems.

**Track R — source discovery.** Which conversation a system finds for a
question. This is not memory quality: a system can return the right
conversation and the superseded version of the fact.

**Track A — answer sufficiency.** Whether the evidence a system returns, under
a token budget identical for every system, lets one fixed reader answer the
question. Implemented in a later plan.

What no published benchmark does today, and what this one is for: a non-English
corpus, the two tracks kept apart, and operability scored with evidence.

Design: `docs/superpowers/specs/2026-09-17-memory-bench-design.md`.

## Run the baseline over the fixture corpus

```bash
uv run membench run \
  --adapter baseline_fts5 \
  --corpus corpora/fixture/corpus.jsonl \
  --questions corpora/fixture/questions.jsonl \
  --out results/fixture-baseline
```

The floor is the point: SQLite FTS5 with no model, no embedding and no
extraction. Every sophisticated system is measured by how far above it lands.
