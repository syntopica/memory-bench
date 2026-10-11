# TODO log

Closed work from `TODO.md`, newest first within each month.

## 2026

### 2026-10

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
