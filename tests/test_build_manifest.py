import sqlite3
from pathlib import Path

from membench.build_manifest import build_manifest
from membench.memory_adapter import ADAPTER_CONTRACT_VERSION
from membench.raw_schema_version import RAW_SCHEMA_VERSION


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
        run_id="r", adapter_name="a", corpus_path=path, questions_path=path, k=1
    )
    assert manifest["track"] == "R: source discovery"


def test_the_manifest_records_the_versions_of_both_published_artifacts(tmp_path: Path):
    path = tmp_path / "f.jsonl"
    path.write_bytes(b"{}")
    manifest = build_manifest(
        run_id="r", adapter_name="a", corpus_path=path, questions_path=path, k=1
    )
    assert manifest["raw_schema_version"] == RAW_SCHEMA_VERSION
    assert manifest["adapter_contract_version"] == ADAPTER_CONTRACT_VERSION


def test_the_manifest_records_the_sqlite_build_that_ran(tmp_path: Path):
    path = tmp_path / "f.jsonl"
    path.write_bytes(b"{}")
    manifest = build_manifest(
        run_id="r", adapter_name="a", corpus_path=path, questions_path=path, k=1
    )
    assert manifest["sqlite_version"] == sqlite3.sqlite_version
