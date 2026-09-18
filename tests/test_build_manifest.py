import sqlite3
from datetime import datetime
from pathlib import Path

from membench.build_manifest import build_manifest
from membench.memory_adapter import ADAPTER_CONTRACT_VERSION
from membench.write_run import RAW_SCHEMA_VERSION

FIXTURE_CORPUS = Path(__file__).resolve().parent.parent / "corpora" / "fixture" / "corpus.jsonl"
FIXTURE_QUESTIONS = (
    Path(__file__).resolve().parent.parent / "corpora" / "fixture" / "questions.jsonl"
)


def test_the_manifest_pins_the_inputs(tmp_path: Path):
    corpus = tmp_path / "corpus.jsonl"
    questions = tmp_path / "questions.jsonl"
    corpus.write_bytes(b"{}")
    questions.write_bytes(b"{}")
    manifest = build_manifest(
        run_id="2026-09-17-abc",
        adapter_name="baseline_fts5",
        corpus_path=corpus,
        questions_path=questions,
        k=10,
        adapter_options={},
    )
    assert manifest["run_id"] == "2026-09-17-abc"
    assert manifest["adapter"] == "baseline_fts5"
    assert manifest["k"] == 10
    assert manifest["corpus"]["path"] == "corpus.jsonl"
    assert len(manifest["corpus"]["sha256"]) == 64
    assert len(manifest["questions"]["sha256"]) == 64


def test_the_manifest_records_the_track_it_scored(tmp_path: Path):
    path = tmp_path / "f.jsonl"
    path.write_bytes(b"{}")
    manifest = build_manifest(
        run_id="r",
        adapter_name="a",
        corpus_path=path,
        questions_path=path,
        k=1,
        adapter_options={},
    )
    assert manifest["track"] == "R: source discovery"


def test_the_manifest_records_the_versions_of_both_published_artifacts(tmp_path: Path):
    path = tmp_path / "f.jsonl"
    path.write_bytes(b"{}")
    manifest = build_manifest(
        run_id="r",
        adapter_name="a",
        corpus_path=path,
        questions_path=path,
        k=1,
        adapter_options={},
    )
    assert manifest["raw_schema_version"] == RAW_SCHEMA_VERSION
    assert manifest["adapter_contract_version"] == ADAPTER_CONTRACT_VERSION


def test_the_manifest_records_the_sqlite_build_that_ran(tmp_path: Path):
    path = tmp_path / "f.jsonl"
    path.write_bytes(b"{}")
    manifest = build_manifest(
        run_id="r",
        adapter_name="a",
        corpus_path=path,
        questions_path=path,
        k=1,
        adapter_options={},
    )
    assert manifest["sqlite_version"] == sqlite3.sqlite_version


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
    manifest = build_manifest(
        run_id="r1",
        adapter_name="baseline_fts5",
        corpus_path=FIXTURE_CORPUS,
        questions_path=FIXTURE_QUESTIONS,
        k=10,
        adapter_options={},
    )
    assert manifest["started_at"].endswith("+00:00")
