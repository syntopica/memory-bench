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

## Writing an adapter

The contract is `membench/memory_adapter.py`, and it is the whole of what a
system under test has to satisfy: `setup`, `ingest`, `query`, `teardown`, plus
the construction rules in `ADAPTER_CONTRACT_VERSION` above them. Read it
before writing code; the docstrings there are normative in a way this section
is not.

**Registration is unbuilt.** There is no plugin mechanism today: the harness
constructs adapters from `ADAPTERS`, a hard-coded dict in
`membench/build_adapter.py`, so a foreign adapter reaches the harness by
adding an entry to that dict in a fork or a patch. That is the honest state,
not a recommendation — what the mechanism should be is a design decision worth
making with two real adapters in hand rather than one. `TODO.md` records it.

What the harness requires of an adapter beyond the method signatures:

- **Construction.** The constructor must be bindable by
  `inspect.signature(...).bind(workspace, **options)`: the workspace `Path`
  first, then every option from `--adapter-options` as a named parameter. The
  binding is checked before anything is written, and an option the constructor
  does not accept is a hard failure rather than an ignored setting — a
  manifest that lists a setting which had no effect describes a run that did
  not happen. Options must be JSON-representable, since they are read from a
  JSON file and recorded verbatim in the manifest.
- **The workspace.** The adapter owns `<out>/workspace/`, exclusively, and
  creates nothing outside it. The harness creates the directory before
  constructing the adapter, and never writes inside it: the run's frozen
  artifacts land in the parent.
- **Source ids.** `source_ids` are matched **verbatim** against the corpus
  `conversation_id`. Exactly one leading `synthesis/` is forgiven, for systems
  that namespace derived records; nothing else is normalised — not case, not
  whitespace, not any other namespace. An id that does not match after that
  one removal is scored as a miss.
- **The `k` slot rule.** `k` bounds ranked source conversations, not pieces of
  evidence: each distinct conversation id spends one slot in the order given,
  deduplicated across the ranking, an unsourced hit spends one too, and
  everything past the k-th slot is discarded before scoring. Cite the
  conversations that actually support a memory, best first — a shotgun
  citation buys nothing and can push the real answer out of the budget.
- **Teardown.** It is called once however the run ends, including after a
  failure part-way through ingest, so it must tolerate a system that was never
  fully set up.

## The token budget, and what a token is

Track A gives every system in a run the same text budget, and the budget is
counted by `membench/count_tokens.py`: **a token is a whitespace-separated run
of characters**. That is deliberately not a model's tokenizer. A budget has to
mean the same thing for every system under test and for a reader checking the
result years later, and no model's tokenizer is stable across versions; what
this definition buys is that every system is charged identically for the same
text.

What it does not buy is fairness between writing systems, and the limit is
stated here rather than discovered later. The counter is only meaningful for
whitespace-delimited scripts. Spanish and English, the two this benchmark
measures, split identically per whitespace run. An unsegmented script does
not: a whole Chinese or Japanese sentence costs one token, so a budget that
binds in Spanish is effectively unbounded there. A run of punctuation is
billable while carrying no content. A corpus in an unsegmented script needs a
different definition, and using this one would hand that system a budget
nobody else got.

Track R passes no budget at all — it scores which conversations were found,
not how much text came back — so nothing on this page's numbers depends on it
yet.

## The result schema

Every line of `raw.jsonl` is one question's Track R result, versioned by
`schema_version` so a row can be read correctly years after the run directory
around it is gone.

- `schema_version`: The `raw.jsonl` row format this row was written under.
- `question_id`: Which question this is.
- `strata`: The question's tags, for descriptive breakdowns only.
- `ranked_sources`: One entry per slot the system spent, best first; `null`
  marks a slot spent by evidence that carried no source conversation.
- `applicability`: `"scored"`, or `"not_applicable"` when the system produced
  no source conversation anywhere in the **whole run**, which leaves the three
  recalls and `reciprocal_rank` `null`. It is a property of the system, not of
  one answer, so every row of a run carries the same value: there is no mixed
  run, and a response that came back without provenance scores the misses it
  earned rather than leaving the denominator. `depth` and `truncated` are
  still reported: they describe the request and the ranking, not the score.
- `depth`: The `k` this run requested and observed; the three recalls and
  `reciprocal_rank` are measured at that depth and mean nothing without it.
- `truncated`: `true` when the system offered more slots than `k` and the
  ranking was cut, so a reader knows a missing later source is the harness's
  choice, not the system's. It means **cut at `k`**, and nothing else: an
  adapter that dropped hits from the end to fit a token budget also cut its
  ranking, and this field still reads `false`. Track R passes no token budget,
  so the two cannot be confused today; Track A will need a signal that says
  which cut fired.
- `recall_at_1`: `1.0` when the answer conversation ranked first.
- `recall_at_5`: `1.0` when it appeared in the first five, `null` when the
  run never looked five deep.
- `recall_at_10`: `1.0` when it appeared in the first ten, `null` when the
  run never looked ten deep.
- `reciprocal_rank`: `1 / rank` of the answer conversation within `depth`,
  `0.0` when it is absent from the observed ranking.
- `seconds`: Wall-clock duration of this single query.
- `evidence_texts`: The evidence as returned, kept so a miss can be read. One
  entry per hit, not per slot, and not cut at `k`, so it is a different length
  from `ranked_sources` by construction: one hit citing three conversations
  spends three slots, and a hit whose slot was truncated away still has its
  text here. The two lists do not align positionally and must not be zipped.

## Flags

- `--adapter` (required): which system under test to run, by name.
- `--corpus` (required): path to the corpus JSONL. Must exist.
- `--questions` (required): path to the labelled question set JSONL. Must exist.
- `--out` (required): directory to write the run's artifacts into.
- `--k` (default `10`): ranking depth requested and scored. It bounds the
  **ranked source conversations**, not the pieces of evidence a system
  returns: each distinct conversation id a hit cites spends one slot, in the
  order given, deduplicated across the whole ranking; a hit that cites nothing
  spends a slot too; and everything past the k-th slot is discarded before
  scoring. One memory citing five conversations therefore costs five of the
  `k`, which is why a consolidated-memory system should cite the conversations
  that actually support the memory rather than every one it was derived from.
  Must be at least 1;
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
