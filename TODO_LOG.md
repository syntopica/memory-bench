# TODO log

Closed work from `TODO.md`, newest first within each month.

## 2026

### 2026-10

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
