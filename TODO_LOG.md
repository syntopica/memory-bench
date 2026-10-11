# TODO log

Closed work from `TODO.md`, newest first within each month.

<!-- tadu:log v1 since 2026-10-12 -->

## 2026

### 2026-10

- [x] 2026-10-11 **A normative specification with a citable revision.**
  Decided 2026-10-11 (owner via Codex adjudication): the shipped adapter and
  result contracts, scoring definitions, run requirements and disclosure rules
  are normative; the specification has numbered revisions and every manifest
  records its revision; design history and rationale stay separate.
  `docs/spec/revision-1.md` states each rule with the code that implements it
  and the test that verifies it (126 cited tests, every one checked to exist;
  rules that bind the system under test or the publisher rather than the
  harness say so). `membench/spec_revision.py` holds `SPEC_REVISION = 1`, and
  manifest `1.2` writes it as `spec_revision`. Checking the rules found one
  unverified claim, that Track R passes an unbounded budget, now covered by
  `tests/test_track_r_token_budget.py`. Evidence: `uv run codeality-py gate`
  passed; `test_the_cited_specification_revision_exists_in_the_repository`.
- [x] 2026-10-11 **A re-run under `--force` clears the adapter's workspace.**
  Decided 2026-10-11 (owner via Codex adjudication): under `--force` the
  harness clears its dedicated adapter workspace before constructing the
  adapter, and the adapter contract version is bumped. `membench/clear_workspace.py`
  removes `<out>/workspace/` (a symlink is unlinked, never followed), and
  `membench/cli.py` calls it under `--force` only after every refusal has
  passed, so a rejected forced run leaves the old workspace untouched.
  `ADAPTER_CONTRACT_VERSION` is now `2.1`: an adapter is always constructed
  on an empty workspace, which a 2.0 adapter can ignore. Evidence:
  `tests/test_clear_workspace.py`, and in `tests/test_validate_run_paths.py`
  a forced re-run over a populated workspace that no longer holds the stale
  file and a refused forced run that keeps it; `uv run codeality-py gate`
  passed.
- [x] 2026-10-11 **The README names the renames the frozen plans still
  use.** A new "Names the plans still use" section maps `index_bytes` to
  `persisted_bytes`, `recall_at_1` to the `recall_any_at_k` /
  `recall_all_at_k` pair, and `answer_conversation_id` to
  `answer_conversation_ids` (the singular key is still accepted on input, as
  `membench/read_answer_labels.py` reads it). This closes both plan-drift
  items, the `index_bytes` one and the four-plan `recall_at_1` one, without
  editing the frozen plans. Evidence: `README.md`; `uv run codeality-py gate`
  passed.
- [x] 2026-10-11 **`reciprocal_rank`'s depth constraint is documented where a
  consumer reads it.** The field keeps its name (renaming it is a schema
  change no published number needed); the README's schema entry and the
  `QuestionResult` docstring now say it is RR at `depth`, give the
  eleventh-rank example, and tell a consumer concatenating runs to group by
  `depth` before averaging. Evidence: `README.md`, `membench/question_result.py`;
  `uv run codeality-py gate` passed, and
  `test_the_fixture_headline_is_exactly_what_the_readme_publishes` still holds.
- [x] 2026-10-11 **`portable_path` no longer depends on the working
  directory.** A file inside a repository is now labelled relative to that
  repository's root (the nearest ancestor holding a `.git` directory or file),
  so `corpora/fixture/corpus.jsonl` keeps its label when a run is launched
  from a subdirectory, and a corpus stored in its own repository outside the
  tree is labelled from that repository's root instead of collapsing to a bare
  `corpus.jsonl`. The working-directory and bare-name fallbacks remain for
  files in no repository. Evidence: `membench/enclosing_repository_root.py`,
  `tests/test_portable_path.py` (two new cases),
  `tests/test_enclosing_repository_root.py`; `uv run codeality-py gate` passed.
