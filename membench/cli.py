"""Command line for running a memory system against a labelled question set."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from membench.adapters.baseline_fts5_adapter import BaselineFts5Adapter
from membench.build_manifest import build_manifest
from membench.load_corpus import load_corpus
from membench.load_questions import load_questions
from membench.run_track_r import run_track_r
from membench.write_run import write_run

_ADAPTERS = {"baseline_fts5": BaselineFts5Adapter}


def main(argv: Sequence[str] | None = None) -> int:
    """Run one system over one corpus and write the run's artifacts.

    Args:
        argv: Command-line arguments, or None to read `sys.argv`.

    Returns:
        0 on success, 2 when the requested adapter does not exist.
    """
    parser = argparse.ArgumentParser(prog="membench")
    subcommands = parser.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run", help="Score one system's source discovery")
    run.add_argument("--adapter", required=True)
    run.add_argument("--corpus", type=Path, required=True)
    run.add_argument("--questions", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--k", type=int, default=10)
    args = parser.parse_args(argv)

    factory = _ADAPTERS.get(args.adapter)
    if factory is None:
        print(f"unknown adapter: {args.adapter}; known: {', '.join(sorted(_ADAPTERS))}")
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    adapter = factory(args.out / "index.db")
    adapter.setup()
    ingest = adapter.ingest(load_corpus(args.corpus))
    results = run_track_r(adapter, load_questions(args.questions), args.k)
    adapter.teardown()

    manifest = build_manifest(
        run_id=args.out.name,
        adapter_name=args.adapter,
        corpus_path=args.corpus,
        questions_path=args.questions,
        k=args.k,
    )
    write_run(args.out, manifest, results, ingest)
    print(f"wrote {args.out}/raw.jsonl and {args.out}/manifest.json")
    return 0
