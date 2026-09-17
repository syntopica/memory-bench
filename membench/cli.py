"""Command line for running a memory system against a labelled question set."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from membench.adapters.baseline_fts5_adapter import BaselineFts5Adapter
from membench.build_manifest import build_manifest
from membench.load_corpus import load_corpus
from membench.load_questions import load_questions
from membench.metric_means import metric_means
from membench.run_track_r import run_track_r
from membench.write_run import write_run

_ADAPTERS = {"baseline_fts5": BaselineFts5Adapter}


def main(argv: Sequence[str] | None = None) -> int:
    """Run one system over one corpus and write the run's artifacts.

    Every failure below exits 2 before creating or touching the output
    directory, so a rejected run cannot leave behind an artifact that
    misrepresents what happened.

    Args:
        argv: Command-line arguments, or None to read `sys.argv`.

    Returns:
        0 on success, 2 when the request cannot produce a run that describes
        itself correctly.
    """
    parser = argparse.ArgumentParser(prog="membench")
    subcommands = parser.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run", help="Score one system's source discovery")
    run.add_argument("--adapter", required=True)
    run.add_argument("--corpus", type=Path, required=True)
    run.add_argument("--questions", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--k", type=int, default=10)
    run.add_argument("--force", action="store_true", help="Overwrite an existing run directory")
    args = parser.parse_args(argv)

    factory = _ADAPTERS.get(args.adapter)
    if factory is None:
        print(f"unknown adapter: {args.adapter}; known: {', '.join(sorted(_ADAPTERS))}")
        return 2

    if args.k < 1:
        print(f"--k must be at least 1, got {args.k}", file=sys.stderr)
        return 2

    if not args.corpus.exists():
        print(f"corpus not found: {args.corpus}", file=sys.stderr)
        return 2

    if not args.questions.exists():
        print(f"questions not found: {args.questions}", file=sys.stderr)
        return 2

    manifest_path = args.out / "manifest.json"
    if manifest_path.exists() and not args.force:
        print(
            f"refusing to overwrite an existing run: {manifest_path} (use --force)",
            file=sys.stderr,
        )
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

    excluded = [result for result in results if result.applicability != "scored"]
    for metric, mean in metric_means(results).items():
        print(f"{metric}@k={args.k}: {'n/a' if mean is None else format(mean, '.4f')}")
    print(
        f"scored {len(results) - len(excluded)} of {len(results)} questions; "
        f"{len(excluded)} excluded as not applicable to Track R"
    )
    return 0
