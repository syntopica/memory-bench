# memory-bench

A two-track benchmark for agent memory systems, in Spanish and English.

Most memory benchmarks collapse the two tracks. A system can surface the
right document and still answer badly, or answer well from the wrong source
and score as correct. Separating them makes it possible to say which half is
failing.

**Track R — source discovery.** Which conversation a system finds for a
question. This is not memory quality: a system can return the right
conversation and the superseded version of the fact.

**Track A — answer sufficiency.** Whether the evidence a system returns, under
a token budget identical for every system, lets one fixed reader answer the
question. Implemented in a later plan.

What no published benchmark does today, and what this one is for: a non-English
corpus, the two tracks kept apart, and operability scored with evidence.
Operability scoring is not implemented either: the capability matrix and its
evidence come with a later plan, as Track A does.

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

This fixture is six conversations, and it is a smoke test, not a result. It
prints `recall_at_5` and `recall_at_10` of `1.0000`, and those two columns are
**saturated, not perfect**: recall@k only discriminates while `k` is far
smaller than the corpus, and a lexical query that ORs its tokens matches
almost everything in six documents. Only `recall_at_1` and the reciprocal rank
separate anything here. A corpus this benchmark reports recall@10 on has to be
large enough for the number to mean something, and a saturated column is
reported as saturated rather than as a tie.

## Flags

- `--adapter` (required): which system under test to run, by name.
- `--corpus` (required): path to the corpus JSONL. Must exist.
- `--questions` (required): path to the labelled question set JSONL. Must exist.
- `--out` (required): directory to write the run's artifacts into.
- `--k` (default `10`): ranking depth requested and scored. Must be at least 1;
  a manifest with a smaller or unbounded `k` than the run it describes is the
  one failure this benchmark cannot tolerate, so `0` or a negative value is
  refused before anything is written. A depth deeper than `k` was never
  observed, so `recall_at_5` and `recall_at_10` are written as `null` rather
  than as misses when `k` is smaller than they are.
- `--force`: overwrite an existing run directory. Without it, a run refuses to
  touch a directory that already holds a `manifest.json`, so a frozen result is
  never silently replaced.

## Licence

MIT.
