# Adapter Contract and Reproducible Manifest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the two things a second memory system cannot be measured against until they are right — the adapter contract and the run manifest — so that adding mem0, Atrium and the rest is an additive change rather than a breaking one.

**Architecture:** Three changes to shapes the repository has already promised to version, plus the one scoring decision `TODO.md` publishes as unresolved. The adapter contract gains a token budget (Track A requires it identical for every system) and a construction contract (the CLI currently assumes every adapter is a class taking one `Path`, which mem0 is not). The manifest gains what reproduction actually needs: when, from which commit, on which interpreter, with which dependency lock and which adapter options. Track R's ranking stops dropping unsourced evidence, which today makes returning material without provenance free and slightly advantageous.

**Tech Stack:** Python >=3.12, uv, pytest, codeality-py. No model calls, no network, no rival adapter — those are later plans.

**Spec:** `docs/superpowers/specs/2026-09-17-memory-bench-design.md`

**Why this plan comes before the corpus and the rivals:** every item here is a breaking change to a published shape. `raw_schema_version` and `adapter_contract_version` both read `1.0` on a public repository as of commit `e19bc50`. Making these changes now costs one major version bump of artifacts nobody has cited; making them after the first comparative result costs the comparability of that result.

## Global Constraints

- Python `>=3.12`, managed with uv. Never invoke `pip` or a system Python.
- One exported unit per file, and the file is named after that unit (codeality-py rule BPY002). A constants-only module trips BPY001: put a constant in the module that owns it.
- `max-file-lines`: 150 soft, 300 hard. Do not raise it.
- Coverage threshold 80. Never lower it to make a gate pass.
- Everything in English: code, comments, identifiers, docstrings, documentation, commit messages.
- Every task runs `uv run codeality-py check` AND `uv run codeality-py gate` before reporting; both must be clean.
- Commit as the human author. No assistant, model, AI-tool, session or co-author trailer of any kind, in any commit message.
- Never hand-write a block labelled as command output. Paste only what you actually ran.
- Do not tune `membench/fts5_query.py` and do not touch `corpora/fixture/`. The lexical floor ORs every token including stopwords, deliberately, and questions `q3` and `q5` are expected to miss at recall@1.
- The fixture headline at `--k 10` must stay `recall_at_1 0.6667`, `recall_at_5 1.0000`, `recall_at_10 1.0000`, `reciprocal_rank 0.8056` unless a task explicitly says otherwise. Task 1 is the one task that changes it, and it says so.

---

### Task 1: An unsourced hit consumes its rank slot

`TODO.md` records this as the sharpest known hole: `membench/ranked_sources.py` keeps only the identifiers it finds, so an adapter returning two unsourced hits above the answer scores `reciprocal_rank` 1.0, while one whose first two hits cite the *wrong* conversations scores 0.333. Returning unsourced material above the answer is therefore free, and slightly advantageous. No adapter in this repository reaches that path today; the first system that consolidates memories will.

**The decision this task implements:** `k` is a retrieval budget, and a piece of evidence spends from it whether or not it carries provenance. An unsourced hit occupies its slot and is published as `null` in the ranking, so a reader sees that the system returned something there and that it could not be scored. Sources within one piece of evidence keep occupying consecutive slots, so a system citing ten conversations in one hit still spends ten slots — that property was won in plan 1 and must not regress.

**Files:**
- Modify: `membench/ranked_sources.py`
- Modify: `membench/question_result.py` (the `ranked_sources` attribute's type and docstring)
- Modify: `membench/recall_at_depth.py`, `membench/reciprocal_rank.py` (they consume the ranking)
- Modify: `membench/write_run.py` (`RAW_SCHEMA_VERSION` to `"2.0"`)
- Test: `tests/test_ranked_sources.py`, `tests/test_run_track_r.py`

**Interfaces:**
- Produces: `ranked_sources(evidence: Sequence[Evidence]) -> tuple[str | None, ...]` — one entry per slot, in rank order; `None` marks a slot spent by evidence with no source conversation. A repeated identifier keeps its first (best) slot and is not emitted again; a `None` is never deduplicated, because two unsourced hits spent two slots.
- Consumed by: `recall_at_depth(ranked, answer, depth)` and `reciprocal_rank(ranked, answer)`, which must both treat `None` as an occupied slot that never matches.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ranked_sources.py
def test_an_unsourced_hit_occupies_its_slot():
    evidence = [
        Evidence(text="no provenance", source_ids=()),
        Evidence(text="no provenance either", source_ids=()),
        Evidence(text="the answer", source_ids=("c1",)),
    ]
    assert ranked_sources(evidence) == (None, None, "c1")


def test_two_unsourced_hits_are_not_deduplicated_into_one_slot():
    evidence = [Evidence(text="a", source_ids=()), Evidence(text="b", source_ids=())]
    assert ranked_sources(evidence) == (None, None)


def test_sources_inside_one_evidence_still_occupy_consecutive_slots():
    evidence = [Evidence(text="crowded", source_ids=("c1", "c2", "c3"))]
    assert ranked_sources(evidence) == ("c1", "c2", "c3")


def test_a_repeated_source_keeps_its_best_slot_only():
    evidence = [
        Evidence(text="first", source_ids=("c1",)),
        Evidence(text="again", source_ids=("c1", "c2")),
    ]
    assert ranked_sources(evidence) == ("c1", "c2")
```

```python
# tests/test_run_track_r.py — add to the existing file
def test_unsourced_hits_above_the_answer_cost_the_system_its_rank():
    """The scoring decision of this task, stated as a test.

    Two systems return the answer as their third piece of evidence. One cites
    wrong conversations first, the other cites nothing first. They must score
    the same: k is a budget, and both spent two slots before the answer.
    """
    wrong_first = _StubAdapter([
        Evidence(text="wrong", source_ids=("c9",)),
        Evidence(text="also wrong", source_ids=("c8",)),
        Evidence(text="the answer", source_ids=("c1",)),
    ])
    unsourced_first = _StubAdapter([
        Evidence(text="no provenance", source_ids=()),
        Evidence(text="no provenance either", source_ids=()),
        Evidence(text="the answer", source_ids=("c1",)),
    ])
    question = Question(question_id="q1", question="?", answer_conversation_id="c1", strata=())

    wrong = run_track_r(wrong_first, [question], 10)[0]
    unsourced = run_track_r(unsourced_first, [question], 10)[0]

    assert wrong.reciprocal_rank == unsourced.reciprocal_rank
    assert unsourced.reciprocal_rank == pytest.approx(1 / 3)
    assert unsourced.applicability == "scored"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_ranked_sources.py tests/test_run_track_r.py -v`
Expected: the four new `ranked_sources` tests fail on the tuple comparison (the current implementation returns `("c1",)` where `(None, None, "c1")` is expected), and the `run_track_r` test fails asserting `1.0 == approx(0.333)`.

- [ ] **Step 3: Implement**

```python
# membench/ranked_sources.py
def ranked_sources(evidence: Sequence[Evidence]) -> tuple[str | None, ...]:
    """Return the ranking the evidence spends its retrieval budget on.

    One entry per slot, best first. A piece of evidence with no source
    conversation spends a slot and appears as None: the system returned
    something there, and it cannot be scored for source discovery. Sources
    inside one piece of evidence spend consecutive slots, so citing many
    conversations at once buys no extra depth. An identifier already seen
    keeps its better slot and is not emitted again; None is never
    deduplicated, because each unsourced hit spent its own slot.
    """
    slots: list[str | None] = []
    seen: set[str] = set()
    for piece in evidence:
        if not piece.source_ids:
            slots.append(None)
            continue
        for raw in piece.source_ids:
            source = normalize_source_id(raw)
            if source in seen:
                continue
            seen.add(source)
            slots.append(source)
    return tuple(slots)
```

`recall_at_depth` and `reciprocal_rank` already compare each entry against the
answer identifier; confirm by reading them that a `None` entry simply never
matches, and widen their parameter annotations to
`Sequence[str | None]`. Do not add an `is not None` guard that skips the slot —
skipping is exactly the defect being removed.

- [ ] **Step 4: Raise the schema version**

In `membench/write_run.py`, set `RAW_SCHEMA_VERSION = "2.0"` and extend its docstring with one line: `2.0 publishes an unsourced hit as a null slot in ranked_sources, where 1.0 dropped it.`

- [ ] **Step 5: Run the whole suite and the fixture**

Run: `uv run pytest` — expect every test to pass.
Run the CLI over `corpora/fixture/` at `--k 10` into a scratch directory under `/tmp`.

**The fixture headline does not move**, because the baseline always carries provenance — every slot it spends is a real conversation id. Confirm `recall_at_1 0.6667`, `recall_at_5 1.0000`, `recall_at_10 1.0000`, `reciprocal_rank 0.8056`, and q3 ranking `['c3', 'c1', 'c5']`. If any of those moved, stop and report it: it would mean this change did more than it was supposed to.

- [ ] **Step 6: Update TODO.md**

Remove the first entry under `## Scoring` (the unsourced-hit hole) — it is now decided and implemented. Leave the `reciprocal_rank` naming entry.

- [ ] **Step 7: Commit**

```bash
git add membench tests TODO.md
git commit -m "feat: an unsourced hit spends its rank slot"
```

---

### Task 2: A token budget in the contract

The spec requires Track A to run "under a token budget identical for every system". The contract has no parameter for it, so adding one later is a major version of a published contract. It is added now, while the only adapter in the tree is one this repository owns.

A budget is only identical across systems if the harness defines the counting. Each adapter counting tokens its own way is not a budget, it is six budgets.

**Files:**
- Create: `membench/count_tokens.py`
- Create: `tests/test_count_tokens.py`
- Modify: `membench/memory_adapter.py` (signature of `query`, `ADAPTER_CONTRACT_VERSION` to `"2.0"`)
- Modify: `membench/adapters/baseline_fts5_adapter.py`
- Modify: `membench/run_track_r.py` (pass the budget through)
- Test: `tests/test_baseline_fts5_adapter.py`, `tests/test_run_track_r.py`

**Interfaces:**
- Produces: `count_tokens(text: str) -> int` — the harness's single definition of a token, so a budget means the same thing for every system.
- Produces: `MemoryAdapter.query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]`. `None` means unbounded, which is what Track R passes: Track R scores which conversations were found, not how much text came back. An adapter must return evidence whose texts sum to at most `token_budget` when one is given, dropping from the end.
- Consumed by: `run_track_r`, which passes `token_budget=None`.

- [ ] **Step 1: Write the failing test for the counter**

```python
# tests/test_count_tokens.py
def test_it_counts_whitespace_separated_words():
    assert count_tokens("quedo en WAL desactivado") == 4


def test_it_counts_nothing_in_an_empty_string():
    assert count_tokens("") == 0
    assert count_tokens("   \n  ") == 0


def test_punctuation_attached_to_a_word_does_not_add_a_token():
    assert count_tokens("¿por que? porque si.") == 4


def test_it_is_language_agnostic():
    """The benchmark's whole differential claim is non-English retrieval.

    A counter that splits Spanish differently from English would make an
    'identical' budget mean two different things.
    """
    assert count_tokens("la base de datos") == count_tokens("the database was here")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_count_tokens.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.count_tokens'`.

- [ ] **Step 3: Implement the counter**

```python
# membench/count_tokens.py
"""The harness's one definition of a token."""


def count_tokens(text: str) -> int:
    """Return the number of tokens in `text`.

    A token is a whitespace-separated run of characters. This is deliberately
    not a model's tokenizer: a budget has to mean the same thing for every
    system under test and for a reader checking the result years later, and no
    model's tokenizer is stable across versions or fair across languages. It
    over-counts nothing and under-counts agglutinative text equally for
    everyone, which is the property a shared budget needs.
    """
    return len(text.split())
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run pytest tests/test_count_tokens.py -v` — expect 4 passed.

- [ ] **Step 5: Write the failing test for the budget in the adapter**

```python
# tests/test_baseline_fts5_adapter.py — add to the existing file
def test_a_budget_drops_evidence_from_the_end(tmp_path):
    adapter = BaselineFts5Adapter(tmp_path / "index.db")
    adapter.setup()
    adapter.ingest([
        Conversation(conversation_id="c1", messages=(Message(role="user", content="wal wal wal"),)),
        Conversation(conversation_id="c2", messages=(Message(role="user", content="wal wal wal"),)),
    ])
    unbounded = adapter.query("wal", 10, None)
    assert len(unbounded) == 2

    bounded = adapter.query("wal", 10, token_budget=3)
    assert len(bounded) == 1
    assert sum(count_tokens(piece.text) for piece in bounded) <= 3
    adapter.teardown()


def test_a_budget_smaller_than_the_first_hit_returns_nothing(tmp_path):
    adapter = BaselineFts5Adapter(tmp_path / "index.db")
    adapter.setup()
    adapter.ingest([
        Conversation(conversation_id="c1", messages=(Message(role="user", content="wal wal wal"),)),
    ])
    assert adapter.query("wal", 10, token_budget=1) == []
    adapter.teardown()
```

- [ ] **Step 6: Run it to verify it fails**

Run: `uv run pytest tests/test_baseline_fts5_adapter.py -v`
Expected: FAIL with `TypeError: query() takes 3 positional arguments but 4 were given`.

- [ ] **Step 7: Implement in the contract and the adapter**

In `membench/memory_adapter.py`, change the signature and the docstring:

```python
    def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
        """Return at most k pieces of evidence, best first.

        `token_budget` is the harness's `count_tokens` applied to the returned
        texts, and it is identical for every system in a run: an adapter
        returns the longest prefix of its ranking that fits, dropping from the
        end. None means unbounded, which is what Track R passes, because Track
        R scores which conversations were found rather than how much text
        came back.
        """
```

Raise `ADAPTER_CONTRACT_VERSION` to `"2.0"` and add one line to its docstring: `2.0 adds the token_budget parameter to query.`

In `membench/adapters/baseline_fts5_adapter.py`, take the new parameter and apply it after the rows are ranked, keeping the prefix that fits. Keep this in the adapter rather than in `run_track_r`: a system that can plan its own retrieval against a budget must be allowed to, and enforcing it centrally would hide that difference.

In `membench/run_track_r.py`, pass `token_budget=None` at the call site.

- [ ] **Step 8: Run the suite and the fixture**

Run: `uv run pytest` — all pass.
Re-run the fixture at `--k 10`: the headline must be unchanged (`0.6667 / 1.0000 / 1.0000 / 0.8056`), because Track R passes no budget.

- [ ] **Step 9: Commit**

```bash
git add membench tests
git commit -m "feat: a token budget every system spends the same way"
```

---

### Task 3: A construction contract

`membench/cli.py:69` calls `factory(args.out / "index.db")`, so every adapter must be a class taking exactly one `Path`. mem0 needs a configuration, a gateway base URL and a pinned release; Atrium needs the path to an instance and a provider. The Protocol published as "the contract" is therefore not sufficient to plug a system in, and the missing half is undocumented.

**Files:**
- Create: `membench/build_adapter.py`
- Create: `membench/load_adapter_options.py`
- Create: `tests/test_build_adapter.py`, `tests/test_load_adapter_options.py`
- Modify: `membench/cli.py` (registry and construction, plus an `--adapter-options` flag)
- Modify: `membench/adapters/baseline_fts5_adapter.py` (accept the workspace and options)
- Modify: `membench/memory_adapter.py` (document construction in the contract's docstring)
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `build_adapter(name: str, workspace: Path, options: Mapping[str, object]) -> MemoryAdapter`. Raises `KeyError` for an unknown name and `TypeError` for an option the adapter does not accept — an unrecognised option is a failure, never a silent no-op, because an option silently ignored is a run configured differently from how its manifest says it was.
- Produces: `load_adapter_options(path: Path | None) -> dict[str, object]` — reads a JSON object, returns `{}` for `None`. Raises `ValueError` when the file is not a JSON object.
- Consumed by: `cli.main`, and by `build_manifest` in Task 4, which records the options.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_build_adapter.py
def test_it_builds_the_baseline_with_its_workspace(tmp_path):
    adapter = build_adapter("baseline_fts5", tmp_path, {})
    assert isinstance(adapter, BaselineFts5Adapter)


def test_an_unknown_adapter_raises(tmp_path):
    with pytest.raises(KeyError):
        build_adapter("nope", tmp_path, {})


def test_an_unrecognised_option_raises_rather_than_being_ignored(tmp_path):
    """A silently ignored option makes the manifest describe a run that did
    not happen."""
    with pytest.raises(TypeError):
        build_adapter("baseline_fts5", tmp_path, {"temperature": 0.7})
```

```python
# tests/test_load_adapter_options.py
def test_no_path_is_no_options():
    assert load_adapter_options(None) == {}


def test_it_reads_a_json_object(tmp_path):
    path = tmp_path / "options.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    assert load_adapter_options(path) == {"a": 1}


def test_a_json_array_is_refused(tmp_path):
    path = tmp_path / "options.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_adapter_options(path)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_build_adapter.py tests/test_load_adapter_options.py -v`
Expected: FAIL, `ModuleNotFoundError` for both new modules.

- [ ] **Step 3: Implement**

`BaselineFts5Adapter.__init__` takes `(self, workspace: Path)` and puts its
database at `workspace / "index.db"` itself — the adapter decides its own
layout, which is the point of giving it a workspace rather than a file path.

```python
# membench/build_adapter.py
_ADAPTERS: dict[str, type] = {"baseline_fts5": BaselineFts5Adapter}


def build_adapter(name: str, workspace: Path, options: Mapping[str, object]) -> MemoryAdapter:
    """Construct the named system under test.

    Every adapter is built from a workspace directory it owns and a mapping of
    options recorded verbatim in the run's manifest. An option the adapter does
    not accept raises rather than being ignored: a run whose manifest lists a
    setting that had no effect describes a run that did not happen.
    """
    adapter_type = _ADAPTERS[name]
    return adapter_type(workspace, **options)
```

`load_adapter_options` reads the file with `json.loads(path.read_text(encoding="utf-8"))` and raises `ValueError(f"adapter options must be a JSON object: {path}")` when the parsed value is not a `dict`.

In `membench/memory_adapter.py`, add a paragraph to the module docstring stating the construction contract: an adapter is a callable taking a workspace `Path` it owns exclusively, plus keyword options recorded in the manifest, and it creates nothing outside that workspace.

- [ ] **Step 4: Wire the CLI**

Replace the `_ADAPTERS` dict and the `factory(...)` call in `membench/cli.py` with `build_adapter`. Add `run.add_argument("--adapter-options", type=Path, default=None, help="JSON object of options for the adapter")`. Validate before creating anything, in the block with the other exit-2 checks: an `--adapter-options` path that does not exist, an unknown adapter name (catch `KeyError`), and a rejected option (catch `TypeError`) each print to stderr and return 2.

```python
# tests/test_cli.py — add
def test_an_unknown_option_exits_2_and_writes_nothing(tmp_path):
    options = tmp_path / "options.json"
    options.write_text('{"nope": 1}', encoding="utf-8")
    out = tmp_path / "run"
    code = main([
        "run", "--adapter", "baseline_fts5",
        "--corpus", "corpora/fixture/corpus.jsonl",
        "--questions", "corpora/fixture/questions.jsonl",
        "--out", str(out), "--adapter-options", str(options),
    ])
    assert code == 2
    assert not out.exists()
```

- [ ] **Step 5: Run the suite and the fixture**

Run: `uv run pytest`. Re-run the fixture at `--k 10` with no `--adapter-options`; the headline is unchanged.

- [ ] **Step 6: Commit**

```bash
git add membench tests
git commit -m "feat: build an adapter from a workspace and recorded options"
```

---

### Task 4: A manifest that reproduces rather than identifies

The spec requires a manifest "covering corpus, questions, labels, source commits, dependency and image locks, prompts, requested and resolved models, adapter configuration and scoring rules". The shipped manifest has the corpus and questions digests, `k`, the adapter name and the SQLite version. `TODO.md` records the gap. Prompts and models belong to the plan that introduces the gateway; everything else is due now, because a second adapter is what makes the dependency set start to vary.

**Files:**
- Create: `membench/harness_commit.py`
- Create: `tests/test_harness_commit.py`
- Modify: `membench/build_manifest.py`
- Modify: `membench/cli.py` (pass the adapter options through)
- Test: `tests/test_build_manifest.py`

**Interfaces:**
- Produces: `harness_commit() -> dict[str, str | bool]` — `{"commit": "<40 hex>", "dirty": bool}`, or `{"commit": "unknown", "dirty": True}` when git is unavailable or the tree is not a repository. It never raises: a manifest that cannot be written is worse than one that admits it does not know.
- Produces: `build_manifest(..., adapter_options: Mapping[str, object]) -> dict` with the new keys below.

- [ ] **Step 1: Write the failing test for the commit probe**

```python
# tests/test_harness_commit.py
def test_it_reports_this_repository_s_commit():
    result = harness_commit()
    assert len(result["commit"]) == 40
    assert set(result["commit"]) <= set("0123456789abcdef")
    assert isinstance(result["dirty"], bool)


def test_it_admits_ignorance_outside_a_repository(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = harness_commit()
    assert result == {"commit": "unknown", "dirty": True}
```

Note for the implementer: the second test depends on `tmp_path` not being
inside this repository. `/tmp` is not, so pytest's default is correct — but
assert nothing about `dirty` being `False`, because a developer's working tree
legitimately varies.

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_harness_commit.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'membench.harness_commit'`.

- [ ] **Step 3: Implement the probe**

Use `subprocess.run` with `["git", "rev-parse", "HEAD"]` and
`["git", "status", "--porcelain"]`, `capture_output=True`, `text=True`,
`check=False`. Treat a non-zero return code, a missing `git`
(`FileNotFoundError`) and empty output all as the unknown case. A dirty tree is
non-empty `status --porcelain` output.

- [ ] **Step 4: Write the failing test for the manifest**

```python
# tests/test_build_manifest.py — add
def test_it_records_what_reproduction_needs():
    manifest = build_manifest(
        run_id="r1",
        adapter_name="baseline_fts5",
        corpus_path=FIXTURE_CORPUS,
        questions_path=FIXTURE_QUESTIONS,
        k=10,
        adapter_options={"seed": 7},
    )
    assert manifest["adapter_options"] == {"seed": 7}
    assert manifest["harness"]["commit"]
    assert manifest["environment"]["python"].startswith("3.1")
    assert manifest["environment"]["platform"]
    assert len(manifest["dependency_lock"]["sha256"]) == 64
    datetime.fromisoformat(manifest["started_at"])


def test_the_timestamp_is_utc_and_explicit():
    manifest = build_manifest(..., adapter_options={})
    assert manifest["started_at"].endswith("+00:00")
```

- [ ] **Step 5: Run it to verify it fails**

Run: `uv run pytest tests/test_build_manifest.py -v`
Expected: FAIL with `TypeError` on the unexpected `adapter_options` argument.

- [ ] **Step 6: Implement**

Add to the returned mapping:

- `"started_at"`: `datetime.now(timezone.utc).isoformat()`.
- `"harness"`: the result of `harness_commit()`.
- `"environment"`: `{"python": platform.python_version(), "platform": platform.platform()}`.
- `"dependency_lock"`: `{"path": "uv.lock", "sha256": sha256_file(<repo root>/uv.lock)}`. Resolve the lock relative to this module's package parent, not the working directory, and record `{"path": "uv.lock", "sha256": "unknown"}` when it is absent — an installed wheel has no lock file beside it.
- `"adapter_options"`: the mapping as given.

Keep the existing keys and their order. Raise `RAW_SCHEMA_VERSION`? No — this
changes the manifest, not the `raw.jsonl` rows. Leave `RAW_SCHEMA_VERSION` at
`"2.0"` from Task 1 and do not invent a manifest version key; the manifest is
identified by `adapter_contract_version` and by its own keys.

In `membench/cli.py`, pass `adapter_options=options` into `build_manifest`.

- [ ] **Step 7: Run the suite and the fixture**

Run: `uv run pytest`. Re-run the fixture; the headline is unchanged, and the
written `manifest.json` now carries `started_at`, `harness`, `environment`,
`dependency_lock` and `adapter_options`. Read the file and check the two
digests still match what plan 1 recorded: corpus `4ed33633…`, questions
`5fae05e9…`.

- [ ] **Step 8: Update TODO.md**

Remove the "A manifest identifies a run's inputs but not its environment"
entry, and narrow the reproduction gap that remains to prompts and models,
which arrive with the gateway.

- [ ] **Step 9: Commit**

```bash
git add membench tests TODO.md
git commit -m "feat: pin when, from where and with what a run happened"
```

---

### Task 5: Say whether the ranking was truncated

`TODO.md`: `raw.jsonl` cuts `ranked_sources` at `k` with no signal, so a reader cannot distinguish "the system returned three sources" from "we asked for three". With Task 1 the ranking now also contains `null` slots, which makes the distinction more valuable, not less.

**Files:**
- Modify: `membench/question_result.py` (new attribute `truncated: bool`)
- Modify: `membench/run_track_r.py`
- Modify: `README.md` (a `## The result schema` section)
- Test: `tests/test_run_track_r.py`

**Interfaces:**
- Produces: `QuestionResult.truncated: bool` — True when the system offered more slots than `k` and the ranking was cut, so a reader knows the absence of a later source is the harness's choice and not the system's.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_run_track_r.py — add
def test_a_cut_ranking_says_it_was_cut():
    adapter = _StubAdapter([Evidence(text="crowded", source_ids=("c1", "c2", "c3", "c4"))])
    question = Question(question_id="q1", question="?", answer_conversation_id="c1", strata=())
    result = run_track_r(adapter, [question], 2)[0]
    assert result.ranked_sources == ("c1", "c2")
    assert result.truncated is True


def test_a_ranking_that_fits_says_it_was_not_cut():
    adapter = _StubAdapter([Evidence(text="one", source_ids=("c1",))])
    question = Question(question_id="q1", question="?", answer_conversation_id="c1", strata=())
    result = run_track_r(adapter, [question], 10)[0]
    assert result.truncated is False
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_run_track_r.py -v`
Expected: FAIL, `AttributeError: 'QuestionResult' object has no attribute 'truncated'`.

- [ ] **Step 3: Implement**

Add the field to `QuestionResult` with a docstring line. In `run_track_r`,
compute the full ranking once, set `truncated = len(full) > k`, and store
`full[:k]`.

- [ ] **Step 4: Document the schema**

Add a `## The result schema` section to `README.md` listing every field of a
`raw.jsonl` row — `schema_version`, `question_id`, `strata`,
`ranked_sources` (with `null` for an unsourced slot), `applicability`,
`depth`, `truncated`, the three recalls, `reciprocal_rank`, `seconds`,
`evidence_texts` — one line each. `TODO.md` records the absence of a published
row schema; this closes it, so remove that entry.

- [ ] **Step 5: Run the suite and the fixture**

Run: `uv run pytest`. Re-run the fixture; the headline is unchanged and every
row now carries `"truncated": false` (the baseline returns at most one source
per conversation over six conversations, so nothing is cut at `k=10`).

- [ ] **Step 6: Commit**

```bash
git add membench tests README.md TODO.md
git commit -m "feat: say when a ranking was cut at k"
```

---

## What this plan deliberately does not do

- **No corpus.** Corpus A is ~120 conversations with human-audited labels and a
  blind critique pass before any label is frozen. It is data production with a
  human gate, not code, and it gets its own plan.
- **No rival adapter and no gateway.** mem0 and Atrium arrive after the
  contract they plug into is stable, which is what this plan makes it.
- **No thresholds.** `THRESHOLDS.md` is derived from a dumb-baseline pilot over
  a corpus that can discriminate, and committed before the first scored run.
  The fixture cannot discriminate: recall@5 and recall@10 are saturated at six
  conversations.
