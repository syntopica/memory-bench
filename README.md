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

## What this release is

Track R and a lexical baseline over a six-conversation fixture. It is not yet a
validated comparative standard: no rival system has been measured, Track A and
operability are unimplemented, and the scoring thresholds do not exist — the
design requires deriving them from a baseline pilot and committing them before
any scored run, precisely so they cannot be chosen once the results are known.
Beating this floor establishes that a system is better than untuned lexical
retrieval, and nothing more.

`docs/superpowers/` holds the design record and the build plan that produced
this. They are published so the reasoning behind every choice can be attacked,
and they are historical: neither was revised as the code corrected it, and each
carries a banner saying where it diverges. A specification with stable
revisions for a result to cite does not exist yet.

Design record: `docs/superpowers/specs/2026-09-17-memory-bench-design.md`.
Known limitations: `TODO.md`.

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

## The result schema

Every line of `raw.jsonl` is one question's Track R result, versioned by
`schema_version` so a row can be read correctly years after the run directory
around it is gone.

- `schema_version`: The `raw.jsonl` row format this row was written under.
- `question_id`: Which question this is.
- `strata`: The question's tags, for descriptive breakdowns only.
- `ranked_sources`: One entry per slot the system spent, best first; `null`
  marks a slot spent by evidence that carried no source conversation.
- `applicability`: `"scored"`, or `"not_applicable"` when the system returned
  evidence with no source conversation anywhere in the full ranking, which
  leaves the three recalls and `reciprocal_rank` `null`. `depth` and
  `truncated` are still reported: they describe the request and the ranking,
  not the score.
- `depth`: The `k` this run requested and observed; the three recalls and
  `reciprocal_rank` are measured at that depth and mean nothing without it.
- `truncated`: `true` when the system offered more slots than `k` and the
  ranking was cut, so a reader knows a missing later source is the harness's
  choice, not the system's.
- `recall_at_1`: `1.0` when the answer conversation ranked first.
- `recall_at_5`: `1.0` when it appeared in the first five, `null` when the
  run never looked five deep.
- `recall_at_10`: `1.0` when it appeared in the first ten, `null` when the
  run never looked ten deep.
- `reciprocal_rank`: `1 / rank` of the answer conversation within `depth`,
  `0.0` when it is absent from the observed ranking.
- `seconds`: Wall-clock duration of this single query.
- `evidence_texts`: The evidence as returned, kept so a miss can be read.

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
- `--adapter-options`: path to a JSON object of options forwarded to the
  adapter's constructor. An option the adapter does not accept is refused
  before anything is written, rather than being silently ignored.

## Licence

MIT.
