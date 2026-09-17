# TODO

Known limitations of the current harness, recorded here rather than left
implicit. Each one was found by review before the first public release and
judged not to block it.

## Scoring

- [ ] **A hit with no source identity is dropped from the ranking instead of
  consuming a rank slot.** `membench/ranked_sources.py` flattens the evidence
  in rank order and keeps only the identifiers it finds, so an adapter that
  returns two unsourced hits above the answer scores `reciprocal_rank` 1.0,
  while one whose first two hits cite the wrong conversations scores 0.333.
  Returning unsourced material above the answer is therefore free, and
  slightly advantageous. No adapter in the repository can reach this path
  today, because the lexical baseline always has provenance — but the first
  system that consolidates memories will. Decide deliberately whether an
  unsourced hit consumes a slot, write the decision into the spec, and test
  it. Changing it is a scoring change, so it is a major version of the
  `raw.jsonl` schema.

- [ ] **`reciprocal_rank` is reciprocal rank at `depth`, under an unqualified
  name.** Every row carries `depth`, and the CLI labels its own output
  `reciprocal_rank@k=<k>`, so the information is not lost. But rows are
  designed to be concatenated across runs, and a consumer that averages a
  `k=2` run together with a `k=10` run mixes two different metrics without
  noticing. Either qualify the field name or document the constraint where a
  consumer will read it.

## Artifacts

- [ ] **`portable_path` is relative to the working directory, not to the
  corpus or the repository.** It succeeds at what it was written for — no
  operator's home path can reach a manifest — but the same corpus labelled
  from a subdirectory, or stored outside the tree, collapses to a bare
  `corpus.jsonl`, which is the name every fixture corpus shares. The sha256
  beside it is the real identity; the label is merely shorter than it should
  be.

- [ ] **A manifest identifies a run's inputs but not its environment.** It
  pins the corpus and question digests, the adapter, `k`, the SQLite version
  and both schema versions. It does not record when the run happened, which
  commit of this harness produced it, or the Python, OS and dependency
  versions underneath. That is enough to identify a run and re-run the
  lexical baseline; it is not enough for a third party to reproduce one. The
  gap matters from the moment a second adapter exists, because that is when
  the dependency set starts to vary.

- [ ] **`raw.jsonl` does not say whether `ranked_sources` was truncated.** It
  is cut at `k` with no signal, so a reader cannot distinguish "the system
  returned three sources" from "we asked for three".

## Documentation

- [ ] **No reader-facing specification with stable revisions to cite.** What a
  result must satisfy, what is merely implemented, what is deferred and what is
  unresolved policy are currently spread across a design record that is not
  normative, a build plan that is historical, this file and the code. A
  benchmark asking to be cited has to let a result name the revision that
  governs it. Splitting the normative rules from the rationale, and giving the
  rules citable revisions, is the work.

- [ ] **The published rationale is a build artifact, not a document written to
  be read.** The two-track argument, the saturation explanation, the untuned
  floor and the threshold-preregistration rule are all in
  `docs/superpowers/specs/`, addressed to the agent that implemented them.
  Restating them for a maintainer of a system being measured is what makes the
  fairness assumptions inspectable — and that restatement must carry the
  inconvenient parts forward, including this benchmark's origin as a comparison
  against its author's own system, or the reframing becomes reputation
  management.

- [ ] **`docs/superpowers/plans/2026-09-17-harness-core-and-baseline.md`
  still documents `index_bytes` as bytes of derived index**, in nine places.
  The field was renamed to `persisted_bytes` precisely because it is not
  that: it stats the whole database, including FTS5's verbatim copy of the
  corpus. The plan is a frozen historical document, but a reader meets the
  contradiction.

- [ ] **No published row schema for `raw.jsonl`.** `RAW_SCHEMA_VERSION` is
  declared and emitted, but `applicability`, `depth` and `schema_version`
  itself are documented only in the code that writes them.

## Measurement, deliberately deferred

- [ ] **`IngestReport` reports one storage number.** The spec requires
  derived-index bytes and total persistent state separately, with equivalent
  boundaries across systems. Those boundaries cannot be defined honestly
  against a single adapter; the definition needs a vector store and a graph
  in hand.

- [ ] **`query(question, k)` takes no token budget**, which Track A requires
  to be identical across systems, and `MemoryAdapter` has no construction
  contract — the CLI assumes every adapter is a class taking one `Path`.
  Both are breaking changes to a published contract once it is published.
