# TODO

Known limitations of the current harness, recorded here rather than left
implicit. Each one was found by review before the first public release and
judged not to block it.

## Scoring

- [ ] **`reciprocal_rank` is reciprocal rank at `depth`, under an unqualified
  name.** Every row carries `depth`, and the CLI labels its own output
  `reciprocal_rank@k=<k>`, so the information is not lost. But rows are
  designed to be concatenated across runs, and a consumer that averages a
  `k=2` run together with a `k=10` run mixes two different metrics without
  noticing. Either qualify the field name or document the constraint where a
  consumer will read it.

- [ ] **No shipped corpus exercises a multi-label or an unanswerable question
  end to end.** `recall_all_*` and the abstention line are covered by unit
  tests and by a CLI test that writes its own question file, but
  `corpora/fixture/questions.jsonl` carries six single-label answerable
  questions, so the paths a real corpus will take through the CLI are proved
  only by tests that construct them. Adding either to the fixture would move
  its published headline, which is deliberately pinned, so the fix belongs
  with LongMemEval-S or Corpus A: the first corpus carrying both must assert
  its own counts rather than inherit this one's confidence.

- [ ] **`reciprocal_rank` reports the best-ranked label, and nothing reports
  the worst.** The rule is published in the field's docstring, in `README.md`
  and in the schema changelog, and it answers "how quickly did the system
  reach the answer". It cannot answer "how far must a reader go to hold the
  whole answer", which is the question a multi-hop result actually raises.
  That is a new metric with its own name when it is wanted, never a
  redefinition of this one.

## Artifacts

- [ ] **`portable_path` is relative to the working directory, not to the
  corpus or the repository.** It succeeds at what it was written for — no
  operator's home path can reach a manifest — but the same corpus labelled
  from a subdirectory, or stored outside the tree, collapses to a bare
  `corpus.jsonl`, which is the name every fixture corpus shares. The sha256
  beside it is the real identity; the label is merely shorter than it should
  be.

- [ ] **The manifest still cannot reproduce a run on its own.** It records
  when the run started, which harness commit produced it (anchored at the
  package's own root, not the caller's working directory), the Python and
  platform versions, the dependency lock's digest, and the adapter options
  applied verbatim, alongside the corpus and question digests, `k`, the
  adapter name and the SQLite version. Four things the design record names are
  still missing. The corpus and questions are hashed but not sourced: a
  `sha256` verifies bytes the reader has no way to obtain, since the label
  beside it is a bare relative path with no repository, URL or commit. The
  adapter under test has no identity beyond its registered name — no version,
  commit or package digest — which is the largest gap the moment a second
  adapter exists. There is no image or container digest. And the prompts
  issued and the models requested and resolved are still absent, which arrive
  with the model gateway.

- [ ] **A re-run does not clear the adapter's workspace, and the likelier
  path needs no `--force` at all.** The harness never clears
  `<out>/workspace/`, so an adapter can inherit whatever a previous run's
  adapter left there, while "ingest into an empty system" is what the contract
  promises. No harness artifact is wrong — the adapter owns its workspace and
  cleans its own state, as the FTS5 baseline does — but a second adapter has
  no way to know what it inherited.

  With `--force` this is deliberate and visible. Without it, it is neither:
  `write_run` is the last thing the CLI does, so any run that fails after
  `workspace.mkdir()` — during setup, ingest or querying — leaves
  `<out>/workspace/` populated and `<out>/manifest.json` absent. The pre-flight
  guard in `validate_run_paths` keys on `manifest.json`, so the next run into
  that directory is not refused and is not warned: it walks into a crashed
  run's leftovers with no flag typed. A crash is the likelier path to a dirty
  workspace, not `--force`.

  Decide whether the harness clears the workspace before constructing an
  adapter, or the contract says an adapter must tolerate a dirty one.

## Contract

- [ ] **There is no mechanism for registering a foreign adapter.** The harness
  builds systems under test from `ADAPTERS`, a hard-coded dict in
  `membench/build_adapter.py`, so a third party reaches the harness only by
  forking or patching that file. This is deferred rather than overlooked: what
  the mechanism should be — an entry point, a dotted-path flag, a manifest
  field — determines what the manifest can record about an adapter's identity,
  and that is worth deciding with two real adapters in hand rather than one.
  The README says plainly that this is the state today.

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

## Measurement, deliberately deferred

- [ ] **`IngestReport` reports one storage number.** The spec requires
  derived-index bytes and total persistent state separately, with equivalent
  boundaries across systems. Those boundaries cannot be defined honestly
  against a single adapter; the definition needs a vector store and a graph
  in hand.

- [ ] **Nothing verifies that an adapter honoured `token_budget`.** The
  comparability of Track A rests entirely on every system being charged the
  same text budget, and no code path ever checks
  `sum(count_tokens(hit.text) for hit in evidence)` against the budget that
  was asked for. An adapter that ignores it, or that repacks its ranking to
  fit more in, is indistinguishable from one that obeyed. Track R passes no
  budget, so nothing published today depends on this; enforcement belongs with
  the gateway and Track A work, which is the first thing that will pass a
  binding budget.

- [ ] **`truncated` cannot say what cut the ranking.** It is
  `len(full_sources) > k`, so it signals the `k` cut alone. Under a binding
  token budget an adapter drops hits from the end and the row still reports
  `truncated: false`, which reads as a ranking that fit. Documented as "cut at
  k" in the schema and the field, which is honest for Track R; Track A will
  need the signal to name which cut fired, and that is a schema change to the
  row.
