"""Write a run's frozen artifacts to disk."""

import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from membench.ingest_report import IngestReport
from membench.question_result import QuestionResult

RAW_SCHEMA_VERSION = "3.0"
"""Version of one `raw.jsonl` row, written onto every row.

Rows travel on their own: they are concatenated across runs, loaded years
apart and re-scored by tools this repository does not own, so the version sits
on each row rather than only on the run directory around it. The major part is
raised whenever a field changes meaning, is removed, or becomes newly
nullable; an added field raises the minor part.

2.0 publishes an unsourced hit as a null slot in ranked_sources, where 1.0
dropped it, and changes what `applicability` means: in 1.0 it was a verdict on
one response, excluding the questions a system answered without provenance; it
is now a verdict on the whole run, identical on every row, and a response
without provenance inside a scored run is a miss rather than an exclusion. A
1.0 consumer that reads the field per row will take the new value for the old
one and report a different number rather than failing, which is why the major
part moved. 2.1 adds `truncated`, which a 2.0 consumer can ignore without
misreading any field it already understood.

3.0 makes a question's answer label a set rather than a single conversation,
and that reaches every metric. `recall_at_1`, `recall_at_5` and `recall_at_10`
are renamed `recall_any_at_1`, `recall_any_at_5` and `recall_any_at_10` - at
least one labelled conversation within the depth - and `recall_all_at_1`,
`recall_all_at_5` and `recall_all_at_10` are added, each 1.0 only when every
labelled conversation is within the depth. The two are reported side by side
and are never averaged into one recall. The rename is deliberately loud: a 2.x
consumer asking for `recall_at_1` will not find the field, which is the good
case, because the alternative is reading `recall_any_at_1` under the old name
and reporting the permissive number as though nothing had changed. On a
single-label question the two recalls coincide, so no number this repository
had already published moves.

`reciprocal_rank` keeps its name and its values on single-label questions, and
its meaning is now stated rather than implied: it is the reciprocal rank of the
**best-ranked** labelled conversation. The worst-ranked one is a different
measurement.

3.0 also adds `answerable`, False exactly when the corpus deliberately cannot
answer the question, and `abstained`, True when the system returned nothing,
False when it returned something and null on an answerable row. Every metric is
null on an unanswerable row - undefined, not unobserved and not a miss - and
that population is reported by its own abstention rate rather than averaged
into the retrieval means.
"""


def write_run(
    out_dir: Path,
    manifest: dict[str, object],
    results: Sequence[QuestionResult],
    ingest: IngestReport,
) -> None:
    """Write `manifest.json` and `raw.jsonl` into the run directory.

    The raw file keeps the evidence text as returned, so a miss can be read
    rather than guessed at, and every row carries the schema version it was
    written under, because rows outlive the run directory around them.

    Args:
        out_dir: Directory for this run; created if missing.
        manifest: The run manifest, extended here with the ingest cost.
        results: One entry per question.
        ingest: What ingesting the corpus cost.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    full_manifest = {**manifest, "ingest": asdict(ingest)}
    (out_dir / "manifest.json").write_text(
        json.dumps(full_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        json.dumps({"schema_version": RAW_SCHEMA_VERSION, **asdict(result)}, ensure_ascii=False)
        for result in results
    ]
    (out_dir / "raw.jsonl").write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")
