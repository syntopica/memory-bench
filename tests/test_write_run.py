import json
from pathlib import Path

from membench.ingest_report import IngestReport
from membench.question_result import QuestionResult
from membench.write_run import RAW_SCHEMA_VERSION, write_run


def _result() -> QuestionResult:
    return QuestionResult(
        question_id="q1",
        strata=("es",),
        ranked_sources=("c5",),
        applicability="scored",
        depth=10,
        recall_at_1=1.0,
        recall_at_5=1.0,
        recall_at_10=1.0,
        reciprocal_rank=1.0,
        seconds=0.01,
        evidence_texts=("body",),
    )


def test_writes_the_manifest_and_one_line_per_question(tmp_path: Path):
    write_run(
        out_dir=tmp_path,
        manifest={"run_id": "r"},
        results=[_result()],
        ingest=IngestReport(seconds=1.0, persisted_bytes=10, input_tokens=0, output_tokens=0),
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == "r"
    assert manifest["ingest"]["persisted_bytes"] == 10
    lines = (tmp_path / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(lines[0])["question_id"] == "q1"
    assert json.loads(lines[0])["evidence_texts"] == ["body"]


def test_creates_the_directory_when_it_is_missing(tmp_path: Path):
    target = tmp_path / "nested" / "run"
    write_run(
        out_dir=target,
        manifest={},
        results=[],
        ingest=IngestReport(seconds=0.0, persisted_bytes=0, input_tokens=0, output_tokens=0),
    )
    assert (target / "raw.jsonl").exists()


def test_every_row_carries_the_schema_version_it_was_written_under(tmp_path: Path):
    write_run(
        out_dir=tmp_path,
        manifest={},
        results=[_result()],
        ingest=IngestReport(seconds=0.0, persisted_bytes=0, input_tokens=0, output_tokens=0),
    )
    row = json.loads((tmp_path / "raw.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["schema_version"] == RAW_SCHEMA_VERSION
