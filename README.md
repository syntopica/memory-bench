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

## Flags

- `--adapter` (required): which system under test to run, by name.
- `--corpus` (required): path to the corpus JSONL. Must exist.
- `--questions` (required): path to the labelled question set JSONL. Must exist.
- `--out` (required): directory to write the run's artifacts into.
- `--k` (default `10`): ranking depth requested and scored. Must be at least 1;
  a manifest with a smaller or unbounded `k` than the run it describes is the
  one failure this benchmark cannot tolerate, so `0` or a negative value is
  refused before anything is written.
- `--force`: overwrite an existing run directory. Without it, a run refuses to
  touch a directory that already holds a `manifest.json`, so a frozen result is
  never silently replaced.
