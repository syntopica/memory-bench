"""Describe a run precisely enough to recompute its report."""

from pathlib import Path

from membench.memory_adapter import ADAPTER_CONTRACT_VERSION
from membench.raw_schema_version import RAW_SCHEMA_VERSION
from membench.sha256_file import sha256_file


def build_manifest(
    run_id: str,
    adapter_name: str,
    corpus_path: Path,
    questions_path: Path,
    k: int,
) -> dict[str, object]:
    """Return the manifest that pins a run's inputs.

    A command line does not say which bytes were read, so the corpus and the
    question set are hashed. Reproducing the report from frozen artifacts and
    rerunning inference are different operations, and this is what makes the
    first one checkable.

    Args:
        run_id: Identity of this run.
        adapter_name: Which system was measured.
        corpus_path: The corpus that was ingested.
        questions_path: The labelled question set that was asked.
        k: Ranking depth requested and scored.

    Returns:
        A JSON-serialisable manifest.
    """
    return {
        "run_id": run_id,
        "track": "R: source discovery",
        "raw_schema_version": RAW_SCHEMA_VERSION,
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "adapter": adapter_name,
        "k": k,
        "corpus": {
            "path": str(corpus_path),
            "sha256": sha256_file(corpus_path),
        },
        "questions": {
            "path": str(questions_path),
            "sha256": sha256_file(questions_path),
        },
    }
