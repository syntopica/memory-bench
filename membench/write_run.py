"""Write a run's frozen artifacts to disk."""

import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from membench.ingest_report import IngestReport
from membench.question_result import QuestionResult

RAW_SCHEMA_VERSION = "1.0"
"""Version of one `raw.jsonl` row, written onto every row.

Rows travel on their own: they are concatenated across runs, loaded years
apart and re-scored by tools this repository does not own, so the version sits
on each row rather than only on the run directory around it. The major part is
raised whenever a field changes meaning, is removed, or becomes newly
nullable; an added field raises the minor part.
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
