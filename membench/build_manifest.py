"""Describe a run precisely enough to recompute its report and rerun it."""

import platform
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from membench.dependency_lock import dependency_lock
from membench.harness_commit import harness_commit
from membench.memory_adapter import ADAPTER_CONTRACT_VERSION
from membench.portable_path import portable_path
from membench.sha256_file import sha256_file
from membench.write_run import RAW_SCHEMA_VERSION


def build_manifest(
    run_id: str,
    adapter_name: str,
    corpus_path: Path,
    questions_path: Path,
    k: int,
    adapter_options: Mapping[str, object],
) -> dict[str, object]:
    """Return the manifest that pins a run's inputs and lets it be reproduced.

    A command line does not say which bytes were read, so the corpus and the
    question set are hashed. The SQLite version is recorded because the
    baseline's tokenizer behaviour is a property of the build that ran it, and
    a lexical floor that moved between two machines must be visible here.
    When the run happened, which harness commit produced it, the interpreter
    and platform underneath, the dependency lock in effect and the options
    given to the adapter are recorded alongside them, because those are what a
    second adapter starts to vary. Reproducing the report from frozen
    artifacts and rerunning inference are different operations, and this is
    what makes the first one checkable.

    Args:
        run_id: Identity of this run.
        adapter_name: Which system was measured.
        corpus_path: The corpus that was ingested.
        questions_path: The labelled question set that was asked.
        k: Ranking depth requested and scored.
        adapter_options: The options passed to the adapter's constructor,
            recorded verbatim.

    Returns:
        A JSON-serialisable manifest.
    """
    return {
        "run_id": run_id,
        "track": "R: source discovery",
        "raw_schema_version": RAW_SCHEMA_VERSION,
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "sqlite_version": sqlite3.sqlite_version,
        "adapter": adapter_name,
        "k": k,
        "corpus": {
            "path": portable_path(corpus_path),
            "sha256": sha256_file(corpus_path),
        },
        "questions": {
            "path": portable_path(questions_path),
            "sha256": sha256_file(questions_path),
        },
        "started_at": datetime.now(UTC).isoformat(),
        "harness": harness_commit(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "dependency_lock": dependency_lock(),
        "adapter_options": adapter_options,
    }
