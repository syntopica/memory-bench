# memory-bench — design

Date: 2026-09-17
Status: approved to start, correcting in flight.

## Purpose

Establish, with evidence, where Atrium is genuinely better than the well-known
agent-memory systems and where it is not. The output is a report scoring each
system 0–5 stars per axis, with the number and the run that produced every star.

The secondary purpose follows from the prior art below: no published benchmark
measures a non-English corpus, separates source discovery from answer
sufficiency, or scores operability with evidence. Those three are the
contribution, and they are what could make this a standard rather than one more
private comparison.

## Prior art, and what we take from it

| project | what it is | why it does not answer the question |
| --- | --- | --- |
| LoCoMo | 81 QA pairs over long multi-session conversations; the set mem0's ECAI 2025 paper uses | companion chat, English, 81 pairs |
| LongMemEval | the set Zep reports (71.2% against mem0's 49%) | English; its evaluator judges generated answers with an LLM |
| [MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench) (ICLR 2026) | adapters already written for `mem0/`, `letta/`, `cognee/`; four competencies including Conflict Resolution | English; no cost, latency or operability; LLM-as-judge; no documented adapter contract |
| [agent-memory-benchmarks](https://github.com/RonsenbergVI/agent-memory-benchmarks) | runnable harness, 8 systems, F1/precision/recall plus p50 latency, per-run API spend in `summary.json` | pre-alpha, 1 star, LoCoMo only, English |

**We do not write adapters that already exist.** Before implementing any
adapter, evaluate MemoryAgentBench's `mem0/`, `letta/` and `cognee/` for
licence compatibility and reuse. Writing our own is the fallback, not the plan.

**We do not write a dataset that already exists** for the English track. LoCoMo
and LongMemEval_s are taken as given.

## The standard claim, and what it obliges

The goal is a superset: everything the existing benchmarks measure, plus the
four things none of them measures. A benchmark that only adds is a private
comparison; a benchmark that also covers is a candidate standard.

| competency | who measures it today | how it lands here |
| --- | --- | --- |
| Accurate retrieval | MemoryAgentBench, LoCoMo, LongMemEval | Track R, plus Track A on the same questions |
| Conflict resolution | MemoryAgentBench | the temporal-contradiction class of corpus A, with statement time and effective time separated |
| Long-range understanding | MemoryAgentBench, LongMemEval | corpus A spans 9 months; questions requiring several conversations are labelled with every answering conversation |
| Test-time learning | MemoryAgentBench | adopted in phase 2 as a competency, not reinvented: the corpus supports it, the harness does not score it yet |
| Multi-session continuity | LoCoMo, agent-memory-benchmarks | corpus A is multi-session by construction |
| Latency and cost | agent-memory-benchmarks | measured at the harness boundary, with attempts and failures separated from successes |
| **Non-English retrieval** | **nobody** | corpus A is Spanish and English; `es` and `en` are first-class strata |
| **Source discovery separated from answer sufficiency** | **nobody** | Tracks R and A, never merged into one number |
| **Operability with evidence** | **nobody** | the capability matrix: rebuild, index loss, offline, upgrade, egress |
| **Technical-work corpus** | **nobody** | decisions, reversals, incidents and versions, not companion chat |

Four obligations follow from claiming this, and they are requirements, not
aspirations:

1. **The adapter contract is published and versioned.** A standard other people
   can run needs a stable `MemoryAdapter` and a stable result schema. Breaking
   either is a major version.
2. **Every result carries its manifest**, so a third party can tell an exact
   report recomputation from a fresh inference run.
3. **The corpus and its labels are published** with the harness. A benchmark
   whose data is private is a blog post.
4. **Where an existing benchmark already measures a competency, we adopt its
   dataset rather than writing a rival one.** LoCoMo and LongMemEval_s are taken
   as given; MemoryAgentBench's adapters are reused if the licence allows.

## What this benchmark measures, in two tracks that are never merged

The single most expensive mistake available here is scoring a retrieval-over-an-
archive system and a memory-rewriting system with one number. They are not the
same kind of thing: Atrium returns passages of a conversation, mem0 returns a
consolidated memory it wrote itself. Hence two tracks.

### Track R — source discovery

Each system returns ranked evidence. The harness maps each hit to the
conversation it came from and scores `recall@1`, `recall@5`, `recall@10` and
MRR against the labelled answer conversation.

- Atrium synthesis records carry `conversation_id = f"synthesis/{...}"`
  (`atrium/ingest/to_synthesis_records.py:33`), so the harness normalises
  `synthesis/<id>` to `<id>` before scoring, and deduplicates.
- A system whose memory has no unique source conversation scores nothing here,
  and that is not a defect of the system. **The report labels this track
  "source discovery" and never calls it memory quality.**
- No nDCG@10. With one binary relevant conversation per question it adds nothing
  over MRR.
- **recall@k only discriminates while `k` is far smaller than the corpus.**
  Measured on the six-conversation fixture: recall@5 and recall@10 were 1.000
  for every system that matched anything at all, because a lexical query ORs its
  tokens and six documents is not enough to separate them. Any corpus this
  benchmark reports recall@10 on must be large enough for the number to mean
  something, and a saturated column is reported as saturated rather than as a
  tie.

### Track A — answer sufficiency

Each system returns its evidence **as text**, under a token budget identical for
every system. One fixed reader answers the question from that evidence alone.
The answer is judged against the seeded fact.

This is the only track in which a consolidated memory and a retrieved passage
can be compared fairly, and it is the track that catches the failure Track R
cannot see: returning the right conversation with the superseded version of the
fact.

Track A is in phase 1. It is the expensive part and it is what makes the
comparison defensible.

## The two model families

Both Claude (through max-lane) and Codex (through the `codex` CLI) are available
on this machine. They are assigned by role, permanently:

| role | family |
| --- | --- |
| generate corpus A | Claude |
| blind critic of corpus A's questions and evidence spans | Codex |
| memory extraction for every system that needs an LLM | Claude, one fixed model for all |
| the single fixed reader in Track A | Codex, the same for all systems |

Hard rules:

- Never one system on Claude and another on Codex.
- Never alternate families on a quota failure. A run that could not get its
  assigned family is a failed run, not a substituted one.
- Cross-family agreement is not ground truth.
- The `codex` CLI is an agent runtime, not a chat-completions server: the reader
  runs with `-s read-only`, `-c 'mcp_servers={}'`, a pinned model and a bound
  output schema, and its structured events and usage are recorded.

## Topology

**Host (macOS).** `model-gateway`, a Node process wrapping max-lane. max-lane
reads Claude Code OAuth tokens from the macOS Keychain and throws on any
non-darwin platform, so it cannot run inside the VM.

The gateway is **not** an OpenAI-compatible server. max-lane accepts one system
string, one user string and one forced tool; it carries no message history, no
tool results, no multiple tools, no streaming, and returns no `stop_reason`.
mem0's OpenAI provider expects extraction JSON in `message.content`, not in a
`tool_use` block. Therefore:

- The gateway implements **only the request subset a pinned mem0 release
  actually emits**, translating the forced-tool input back into
  `message.content`, and returns a loud error for anything outside that subset.
- It never silently degrades. Disabling mem0's extraction to make the
  integration pass is forbidden.
- **Gate:** fixtures for add / search / update / reversal must pass before any
  scored run.

**Embeddings.** Each system runs its **native** embedder in the headline table.
Atrium's is embeddinggemma-300m ONNX q8 on CPU, 384 dims via Matryoshka
truncation, with a fixed prefix (`atrium/embed/embedder.py`). Forcing a shared
embedder would not remove a variable; it would evaluate a different product.
The measurement in that file is the reason: the English-only default of the
previous system scored dense R@10 40.8% on a 365-pair set that is 77% Spanish,
and the current multilingual model scored 70.4% at the same 384 dims.

A shared-embedder ablation may follow later, with a multilingual model, both
sides re-embedded and dimensions asserted. It is not in phase 1.

**VM.** One OrbStack machine, `membench`. OrbStack machines share a single Linux
VM and kernel, so restarting one does not clear host caches and the design claims
no such thing. *Isolated* machines cannot reach the host, which would make the
gateway unreachable, so `membench` is a normal machine reaching the host at
`host.orb.internal`, with an explicit egress policy, per-container resource
limits, and model artifacts preloaded before egress is cut. The spec requires
verifying from inside the containers that the gateway is reachable and that
forbidden egress fails. Per-system reset is fresh volumes or a clone of a
stopped machine — not a snapshot claimed to reset the kernel.

## Corpora

### Corpus A — synthetic, Spanish and English

One fictional project, ~6 people, ~120 conversations over 9 months, generated by
Claude with a fixed seed and committed as a versioned artifact so a rerun needs
no model call.

Seeded on purpose: decisions **and their later reversals**, incidents, personal
preferences, changes of opinion.

Requirements that a seeded fact alone does not satisfy:

- A human audits the evidence spans and the questions. A seeded fact is not
  proof that the generated dialogue states it unambiguously.
- Codex criticises the drafts blind, before any label is frozen.
- Labels are frozen before any system is tuned.
- The corpus freezes an **as-of date**, and contradiction questions distinguish
  **statement time** from **effective time**. "The second version wins" is not a
  specification.
- Conversations are ingested chronologically, with checkpoints before and after
  each reversal.
- The question set includes historical questions ("what did we believe in
  March") and unanswerable questions.
- Development questions and held-out questions are separate sets.
- The `note` stratum either gets generated notes or is removed. Conversations
  alone do not support it.

Strata follow `~/p/atrium/benchmarks/acceptance/README.md`: `es|en`,
`conversation|note`, `overlap|no-overlap`, `recent|old`, plus the new
**temporal-contradiction** class.

**Statistical honesty.** 80 questions across four binary strata is roughly five
per cell. Per-stratum results are reported as descriptive, with cell counts and
paired uncertainty, and never as a per-stratum star. Where the sample cannot
separate two thresholds, the star is reported as **inconclusive**.

### Corpus B — public

LongMemEval_s, reported separately and never merged with A. Its evaluator judges
generated answers with an LLM, so it lands in Track A with a pinned judge, in an
explicitly LLM-judged table outside the judge-free headline. Published scores
from mem0 and Zep are contextual references, not comparisons: a different
reader, prompt, retrieval budget or product version makes them incomparable.

## Systems, and how each is set up

Phase 1: the dumb baseline, Atrium, mem0. Phase 2, against the same harness and
only after phase 1 passes its gates: Zep/Graphiti, Letta, cognee, supermemory,
mempalace.

**Dumb baseline.** SQLite FTS5 plus grep over the same corpus. Without it no
number means anything: it bounds how much any sophisticated system actually adds.

**Atrium.** The naive setup evaluates Atrium switched off: only `note` and
`synthesis` roles are embedded (`atrium/embed/semantic_roles.py:8`), so ingesting
raw conversations and running `embed` leaves the corpus with no vectors and the
adaptive search falls back to lexical. The full setup is therefore:

1. convert corpus to the canonical archive format
2. `atrium ingest`
3. `atrium synthesize` through a metered provider
4. `atrium ingest-synthesis`
5. `atrium embed`
6. assert eligible-record and vector counts before any query

Synthesis cost is charged to ingestion. A raw-only configuration is kept as an
ablation, labelled as such. Note that `atrium/synthesize/max_lane_call.py` and
`codex_lane_call.py` call Anthropic directly or launch Codex, bypassing the
gateway, so their cost is metered separately.

The adapter imports `atrium.retrieve.search.search` directly. `atrium search`
has no `--json` (`atrium/cli.py:176-186`), and parsing stdout would be fragile.

**mem0.** `Memory.from_config` with `llm.provider=openai` and `openai_base_url`
pointed at the gateway, its native embedder, a persistent store on disk, and a
consistent identity scope. The mem0 release is pinned.

## Adapter contract

```
setup()                      -> None
ingest(corpus)               -> IngestReport
query(question, k)           -> list[Evidence]
teardown()                   -> None
```

`Evidence` carries the text, the system's native id, the source conversation
ids and the timestamps. Track R scores the source ids; Track A reads the text.
A system without provenance is not scored zero for lacking it — it simply does
not appear in Track R.

## Measurement

**Latency** is timed at the harness boundary, not at the gateway: the lexical
baseline never touches the gateway, and local embedding and Atrium's own
providers bypass it. System blocks are interleaved rather than run in sequence,
so provider load and quota do not confound one system. Process-cold and
host-cold are defined separately. With five repetitions the report gives p50 and
maximum; a p95 requires enough samples to support one.

**Cost** separates counted tokens from a priced estimate. Attempts, failures,
cache usage and embedding work are recorded separately; max-lane rotates
credentials on 429/5xx, so the gateway instruments attempts, not just successes.

**Storage** reports derived-index bytes and total required persistent state
separately, with equivalent boundaries across systems (archives, synthesis
registries and history stores included).

**Operability** is a capability matrix with evidence, not stars. The eight
yes/no questions of the first draft encoded Atrium's architecture as the correct
answer. The matrix carries unknown and not-applicable states, a declared
preference direction, phase-specific outcomes (offline retrieval is not offline
ingestion), and recovery measured against the same loss scenario and the same
allowed backups, reporting restored quality, time and cost. Upgrades are tested
between named versions. A blocked telemetry request is not evidence of absent
telemetry.

## Scoring

Stars 0–5 on quality, cost and latency only. No weighted overall score: an
average hides the axis that matters. Where the sample cannot separate two
thresholds the cell reads **inconclusive**.

Thresholds are not in this document, because they are not yet knowable. They go
in `THRESHOLDS.md`, committed before the first scored run and derived **only**
from the dumb baseline pilot — never from a competitor's result, which is how a
threshold gets fitted to the winner one wants. Once committed they are not
changed for that run; changing them starts a new run id.

## Output

`results/<run-id>/` holds `raw.jsonl` — retrieved text, model responses,
failures and timings — and a hashed manifest covering corpus, questions, labels,
source commits, dependency and image locks, prompts, requested and resolved
models, adapter configuration and scoring rules. One command recomputes
`report.md` from the frozen artifacts. Reproducing the report exactly and
rerunning inference are distinguished, because a command alone does not capture
mutable provider defaults or model aliases.

## Declared bias

Corpus A is model-generated, which favours systems that use the same model
family to extract memories. The dumb baseline and corpus B bound that, and the
Codex critic pass bounds the question-phrasing half of it. It is not eliminated,
and the report says so.

## Gates before any scored run

1. Adapter fixtures green: add / search / update / reversal for mem0.
2. Atrium record and vector counts asserted non-zero for the semantic roles.
3. Gateway reachable from inside the containers; forbidden egress verified to
   fail.
4. Corpus A labels frozen after the human audit and the Codex critic pass.
5. Thresholds pre-registered.

## Out of scope for phase 1

Zep, Letta, cognee, supermemory, mempalace; the shared-embedder ablation; a full
two-model factorial; any claim of comparability with published leaderboard
numbers.
