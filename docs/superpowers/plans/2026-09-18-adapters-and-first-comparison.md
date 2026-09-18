# Adapters and the First Comparison — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure a real memory system. Produce the first Track R comparison —
Atrium against mem0 against the untuned lexical floor — on a public corpus this
repository did not write, with every fairness concession stated in the report.

**Architecture:** LongMemEval_s supplies the corpus and the labels, so no
corpus has to be written before a number exists. Atrium needs no model service
at all — its embeddings are local ONNX — so the model gateway exists for mem0
and whatever follows it, and its job is to record what was actually requested
and resolved rather than to isolate anything. Each adapter is a thin wrapper
over the published package, never a vendored copy.

**Tech Stack:** Python 3.12+, uv, pytest, codeality-py. `mem0ai` from PyPI.
Atrium from its own checkout. LongMemEval_s from the MIT dataset release.

**Spec:** `docs/superpowers/specs/2026-09-17-memory-bench-design.md` — sections
"Corpus B — public", "Licences, verified 2026-09-18", "Systems, and how each is
set up", "Gates before any scored run", "Declared bias".

**Sibling plan:** `docs/superpowers/plans/2026-09-18-corpus-a-and-thresholds.md`.
Its Tasks 1-4 (unanswerable questions, abstention, strata vocabulary, corpus
provenance) are prerequisites of this plan and are being done first. Its Tasks
5-9 (Corpus A's content and the threshold pilot) are parked until this lands.

## Global Constraints

- One exported unit and one primary responsibility per source file.
- `uv run pytest` passes, `uv run codeality-py check` reports 0 findings,
  `uv run codeality-py gate` stays green. Coverage threshold 80.
- Commit messages imperative, English, no assistant attribution, no co-author
  trailers.
- TDD: failing test, watch it fail, implement, watch it pass.
- Published shapes carry versions and honest changelogs:
  `RAW_SCHEMA_VERSION`, `ADAPTER_CONTRACT_VERSION`, `MANIFEST_VERSION`. A
  change of meaning to an existing field is a major change and is recorded.
- No artifact may misrepresent its own run. A number that was not observed is
  `null`, never `0.0`. A rule that is scored is published in the contract.
- **Adapters are thin wrappers over published packages.** The spec's licence
  review found MemoryAgentBench's "adapters" are vendored whole upstream
  projects; this repository does not do that, and an adapter must be able to
  state which released version it measured.
- **No competitor's result may influence a threshold, a prompt or a tuning
  decision.** Thresholds come from the baseline pilot alone.

## Rulings made before this plan

**R1 — no containers in this plan.** The spec's gate 3 wants the gateway
reachable from inside containers with forbidden egress verified to fail.
Container isolation changes no retrieval score; it changes the operability
matrix. It moves to the operability plan. What this plan does take from that
gate is the part that *does* affect a score: the gateway records the model
actually resolved, so a system cannot be measured against a model it did not
use, and the report states that egress was not restricted.

**R2 — gate 1 is corrected, because mem0 v3 has no update.** The spec asks for
`add / search / update / reversal` fixtures. mem0 v3 is single-pass and
ADD-only by its own migration guide: UPDATE and DELETE were removed, and
deduplication is hash-based. The fixture set becomes `add / search / reversal /
dedup-collision`. The reversal fixture matters more than ever — with no update
path, a later contradicting fact does not replace an earlier one, and how the
system ranks the two is exactly what Track R should expose. The dedup fixture
is new and is a measurement hazard, not a feature: if two conversations extract
to a byte-identical fact, the second add is dropped and that conversation loses
its provenance, which would read as a retrieval failure that is really an
ingestion collision. Measure it and report it rather than discovering it inside
a score.

**R3 — a question may have more than one labelled answer conversation.**
LongMemEval labels `answer_session_ids`, plural. Keeping the harness's single
label would mean dropping its multi-session questions, which are precisely the
multi-hop ones, and a benchmark that silently drops the hard questions reports
a number that is not what it claims. The label widens to a set, and recall is
reported twice and never merged: **any** (at least one labelled session in the
top k) and **all** (every labelled session in the top k). For a single-label
question the two are identical by construction, so nothing about the fixture or
Corpus A moves.

**R4 — mem0 is measured on a corpus it publishes gains against.** mem0 v3's own
release notes claim improvements on LongMemEval. That is its home ground, and
the report says so beside the number rather than in a footnote. This is not a
reason to avoid the corpus — a result on the rival's home ground is worth more
than one on ours — but an unstated advantage is a misrepresentation.

**R5 — provenance for mem0 is supplied by the adapter, deliberately and
visibly.** mem0 returns a memory id, not the conversation a memory came from.
The adapter ingests one conversation per `add()` call with
`metadata={"conversation_id": ...}` and reads it back from the search result.
This is the honest reading of "cite the conversations that support the memory",
and the adapter's docstring must state that the provenance is the adapter's
construction, not a mem0 feature, so nobody later reports it as one.

---

## Task 1: Ingest LongMemEval_s into the harness format

**Files:**
- Create: `tools/ingest_longmemeval.py`, `corpora/longmemeval-s/README.md`
- Create: `corpora/longmemeval-s/corpus.jsonl`, `questions.jsonl`
- Test: `tests/test_ingest_longmemeval.py`

**Three things were established before this task was written, by querying the
Hugging Face API directly on 2026-09-18. Do not re-derive them; do verify the
digests.**

1. **Take the cleaned release, not the original.** `xiaowu0162/longmemeval-cleaned`
   is MIT and its own card says it "replaces the original LongMemEval dataset",
   removing "noisy history sessions that interfere with the answer
   correctness". The author superseded their own data. Using the original would
   measure against labels its author has withdrawn. Record this in the corpus
   README, and record the consequence the spec's comparability section needs: a
   system's published LongMemEval score may have been obtained against the
   noisy release, which is one more reason those numbers are context and not
   comparisons.
2. **The corpus is not committed.** `longmemeval_s_cleaned.json` is 277,383,467
   bytes. Committing it, or a conversion of it, would put a quarter of a
   gigabyte into a public repository for no gain. Instead `tools/ingest_longmemeval.py`
   fetches and converts, the output is git-ignored, and the manifest records
   the upstream dataset revision, the converter's commit and the sha256 of the
   file actually produced. Unlike Corpus A, this corpus **is** bit-reproducible
   from a pinned upstream revision, and the README should say so — the two
   corpora make opposite claims and a reader must not carry one over.
3. **`longmemeval_oracle.json` is 15,388,478 bytes and holds only the answer
   sessions.** Use it as the fast end-to-end smoke corpus: it exercises the
   whole pipeline in minutes, and a retrieval score against it is meaningless
   and must never be published as a result.

Then **read the real dataset** and record its actual shape in the README: how a
session, its turns and its `answer_session_ids` are keyed, whether `has_answer`
is per-turn, how many questions carry more than one answer session, and how
many are abstention questions. If the data disagrees with any of the above,
stop and report rather than adapting the labels to fit.

Map: one LongMemEval session becomes one `Conversation`; its `session_id`
becomes `conversation_id`; its turns become `Message`s. One question becomes a
`Question` whose labelled answers are its `answer_session_ids`. An abstention
question — one the corpus cannot answer — maps to the unanswerable question the
sibling plan's Task 1 introduced.

Strata: every question is tagged `en` and `conversation`. The `overlap` and
`recent|old` dimensions must be **derived from the data and the derivation
documented**, not guessed: `recent|old` from the session's position in the
corpus timeline, `overlap|no-overlap` from a stated lexical criterion between
the answer session and its competitors. If a dimension cannot be derived
honestly, say so in the README and leave it out — a fabricated stratum is worse
than a missing one, and `validate_strata` will reject a question that omits a
required dimension, so this is a real decision, not a formality.

Licence: LongMemEval is MIT and its filler sessions derive from ShareGPT
(Apache-2.0) and UltraChat (MIT). The README carries all three notices.

- [ ] **Step 1: Read the dataset; write the README's shape section**
- [ ] **Step 2: TDD the converter against a hand-written miniature fixture**
- [ ] **Step 3: Convert; verify it loads**

```bash
uv run python -c "
from pathlib import Path
from membench.load_corpus import load_corpus
from membench.load_questions import load_questions
c = load_corpus(Path('corpora/longmemeval-s/corpus.jsonl'))
q = load_questions(Path('corpora/longmemeval-s/questions.jsonl'))
print(len(c),'conversations', len(q),'questions')
print('unanswerable', sum(1 for x in q if not x.answer_conversation_ids))
print('multi-answer', sum(1 for x in q if len(x.answer_conversation_ids) > 1))
"
```

- [ ] **Step 4: Commit**

---

## Task 2: A question may have several labelled answers

**Files:**
- Modify: `membench/question.py`, `membench/load_questions.py`,
  `membench/recall_at_k.py`, `membench/recall_at_depth.py`,
  `membench/reciprocal_rank.py`, `membench/question_result.py`,
  `membench/run_track_r.py`, `membench/metric_means.py`,
  `membench/write_run.py`, `README.md`
- Test: the matching test modules

This is R3 in code, and it is a breaking change to a published contract done
deliberately. `answer_conversation_id: str | None` becomes
`answer_conversation_ids: tuple[str, ...]`, empty for an unanswerable question.
The `None` case disappears: an empty set *is* the unanswerable case, which
removes the `None`-matching hazard the sibling plan's Task 1 had to guard
against rather than leaving two representations of absence.

Metrics, reported separately and never merged:
- `recall_at_1/5/10` become `recall_any_at_*` — at least one labelled
  conversation within the depth.
- New `recall_all_at_*` — every labelled conversation within the depth.
- `reciprocal_rank` uses the **best-ranked** labelled conversation, and its
  docstring says so: the alternative (the worst) is a different measurement and
  would silently change every published number.
- For a single-label question all three coincide, so the fixture's headline
  must not move: `0.6667 / 1.0000 / 1.0000 / 0.8056`.

Version discipline: `RAW_SCHEMA_VERSION` takes a **major** bump — three fields
are renamed and one metric's meaning is now explicit — with a changelog that
says a consumer reading `recall_at_1` will not find it rather than silently
reading something else. `ADAPTER_CONTRACT_VERSION` does **not** move: no
adapter sees a question's label.

Update `README.md`'s schema section in the same commit. The last time a rule
changed and only its own unit was updated, four published statements went
false; that is the failure this repository has already made once.

- [ ] **Step 1: Write the failing tests, including that single-label questions are unmoved**
- [ ] **Step 2: Run to verify they fail**
- [ ] **Step 3: Implement across the metric units**
- [ ] **Step 4: `uv run pytest`, `codeality-py gate`, and the fixture run unmoved**
- [ ] **Step 5: Commit**

---

## Task 3: The model gateway

**Files:**
- Create: `membench/model_gateway.py`, `membench/model_call_record.py`
- Modify: `membench/build_manifest.py`, `membench/cli.py`
- Test: `tests/test_model_gateway.py`

Not a proxy server and not a container boundary (R1). It is the single object
every adapter that needs a model is handed, and its job is that the run can say
what was actually used.

It records, per call: the model **requested** and the model **resolved** (a
provider alias can silently resolve elsewhere, which is why the spec separates
them), the prompt, the token counts, the latency, and any error. The records
land in the run directory beside `raw.jsonl`; the manifest carries the
aggregate — models seen, call counts, total tokens — and the exact provider
endpoint base, never a credential.

**Credentials are read from the environment and never recorded, printed or
committed.** The manifest records that a key was present, not its value or any
prefix of it.

Configuration is per run, pinned in the manifest: an extraction model and an
embedding model, each named exactly, so a rerun can say whether it used the
same one. A provider default that moves under the benchmark is exactly the
mutable state the spec says a command alone does not capture.

- [ ] **Step 1: TDD against a stub provider; no network in tests**
- [ ] **Step 2: Implement; bump `MANIFEST_VERSION`'s minor with its changelog**
- [ ] **Step 3: Commit**

---

## Task 4: The Atrium adapter

**Files:**
- Create: `membench/adapters/atrium_adapter.py`
- Modify: `membench/build_adapter.py`, `README.md`, `TODO.md`
- Test: `tests/test_atrium_adapter.py`

Atrium's own CLI help calls itself "the core surface every adapter wraps", and
its dependencies are `onnxruntime`, `tokenizers` and `huggingface_hub` — the
embeddings are local. **It therefore takes no gateway**, and that is a finding
the report states rather than an omission: it is the difference between a system
that can run offline and one that cannot, which is an operability axis result
arriving early.

`setup()` creates an index inside the adapter's workspace. `ingest()` writes the
corpus as Atrium's canonical archive and runs `ingest` then `embed`. `query()`
calls `search` and maps each hit to `Evidence` with the conversation id as its
source.

Two things to establish and record in the docstring, not assume:
- Which search lane is measured. Atrium offers fused, `--words` and `--dense`.
  **Ruling: the default fused lane is the system under test**, because that is
  what a user of Atrium gets. The two single lanes are worth recording as
  context, run separately under their own adapter names rather than blended
  into one number.
- That the corpus is ingested chronologically, as the contract requires.

Spec gate 2 belongs here: assert the record and vector counts are non-zero for
the semantic roles after ingest, and fail loudly if not. A system that silently
ingested nothing would score zero and look like a bad system.

**Declare the conflict of interest in `README.md`.** Atrium is this
repository's author's own system. The design record already concedes the
benchmark's origin; the adapter is where a reader checks whether it was given
an advantage, so the adapter must be as thin as mem0's and the README must say
where to look.

- [ ] **Step 1: TDD with a miniature corpus against a real Atrium checkout**
- [ ] **Step 2: Implement; register it; gate 2 assertion with its own test**
- [ ] **Step 3: Commit**

---

## Task 5: The mem0 adapter

**Files:**
- Create: `membench/adapters/mem0_adapter.py`
- Modify: `membench/build_adapter.py`, `pyproject.toml`, `README.md`
- Test: `tests/test_mem0_adapter.py`

A thin wrapper over the published `mem0ai` package, pinned to an exact released
version recorded in the manifest. Never a vendored copy.

`ingest()` calls `add()` **once per conversation**, with the conversation's
messages and `metadata={"conversation_id": ...}`, chronologically. `query()`
calls `search()` and reads the conversation id back out of each result's
metadata (R5). The docstring states plainly that this provenance is the
adapter's construction and not a mem0 feature — mem0 returns a memory id, not a
source conversation — so no reader takes it for one.

Known hazards to handle explicitly and record, not discover in a score:
- **Hash deduplication.** A byte-identical extracted fact from a second
  conversation is dropped, and that conversation loses its provenance. Count
  the adds that produced no new memory and report the number in
  `IngestReport`. It is an ingestion collision, not a retrieval failure.
- **Consolidation.** If a returned memory carries more than one conversation,
  emit them all in `source_ids` and let the k-slot rule apply — the contract
  already publishes that attaching N conversations to one memory spends N of
  the k, and mem0 is the shape that rule was written for.
- **No update path.** v3 is ADD-only; do not write code that assumes an update
  or delete exists.

`query()` must honour `token_budget` by the published rule — the longest prefix
of the ranking that fits, dropped from the end, never re-ranked to pack better.

Tests use a stub in place of the network. A real end-to-end run against the
provider is Task 6, not a unit test.

- [ ] **Step 1: TDD against a stubbed mem0 client**
- [ ] **Step 2: Implement; register it; pin the version**
- [ ] **Step 3: Commit**

---

## Task 6: Adapter fixtures — gate 1, corrected

**Files:**
- Create: `tests/fixtures/adapter_behaviour/` and its test module

Gate 1 of the spec, with R2's correction. Four behaviours, each a named fixture
run against **every** registered adapter so the suite is a contract test rather
than a mem0 test:

1. **add** — a conversation ingested is retrievable by its own vocabulary.
2. **search** — the right conversation outranks a competitor sharing much of
   its vocabulary.
3. **reversal** — a fact stated and later reversed: both conversations are
   retrievable, and the run records which ranks higher. There is no correct
   answer asserted here; the fixture exists to make the behaviour visible,
   because with no update path the two coexist and how a system ranks them is a
   real difference between systems.
4. **dedup-collision** — the same fact stated in two conversations: assert the
   adapter reports the collision rather than silently losing the second
   conversation's provenance.

The baseline must pass all four; a lexical index has no extraction step, so
3 and 4 are trivially true for it, and that is itself the contrast worth seeing.

- [ ] **Step 1: Write the fixtures and the parameterised contract test**
- [ ] **Step 2: Run against every registered adapter; record the differences**
- [ ] **Step 3: Commit**

---

## Task 7: The first comparison

**Files:**
- Create: `results/longmemeval-s-<adapter>/` per system (git-ignored),
  `docs/results/2026-XX-first-comparison.md`
- Modify: `README.md`, `TODO.md`

Run all three systems over LongMemEval_s with identical `k` and identical
token budget, and write the report.

```bash
for a in baseline_fts5 atrium mem0; do
  uv run membench run --adapter "$a" \
    --corpus corpora/longmemeval-s/corpus.jsonl \
    --questions corpora/longmemeval-s/questions.jsonl \
    --out "results/longmemeval-s-$a" --k 10
done
```

The report states, beside the numbers and not beneath them:
- that mem0 publishes gains on this corpus and it is therefore its home ground
  (R4);
- that Atrium is the author's own system, and where a reader checks the
  adapters for asymmetry;
- that Atrium required no model service and mem0 did, with what each cost;
- that egress was not restricted (R1);
- the ingestion collisions mem0 reported, so a retrieval number is not read as
  including them;
- that no thresholds exist yet, so **no stars are awarded** — this is a table of
  measurements, not a ranking;
- `recall_any` and `recall_all` separately, never averaged together.

**Do not tune anything after seeing a number.** If a system underperforms in a
way that looks like a wiring bug rather than a result, that is a defect to fix
and re-run from scratch with the fix recorded — not a tuning pass. Say which
happened.

- [ ] **Step 1: Run all three; keep every artifact**
- [ ] **Step 2: Write the report; publish it**
- [ ] **Step 3: Commit and push**

---

## Self-review

**Spec coverage.** Corpus B/LongMemEval as a judge-free Track R corpus, Task 1.
Gate 1 fixtures, Task 6 with R2's correction. Gate 2 Atrium counts, Task 4.
Gate 3 gateway, Task 3, with containers deferred by R1 and the deferral stated.
Gates 4 and 5 (Corpus A's audit, pre-registered thresholds) belong to the
sibling plan and are why Task 7 awards no stars. Declared bias, Task 7.

**Out of scope, deliberately:** Corpus A, thresholds and stars; Track A and any
LLM judge; Zep, Letta, cognee, supermemory, mempalace; containers and egress
verification; the shared-embedder ablation. This plan produces the first honest
measurement of a real memory system, which is the thing the project exists for
and does not yet have.
