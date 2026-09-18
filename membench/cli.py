"""Command line for running a memory system against a labelled question set."""

import argparse
import inspect
import sys
from collections.abc import Sequence
from pathlib import Path

from membench.build_adapter import ADAPTERS, build_adapter
from membench.build_manifest import build_manifest
from membench.load_corpus import load_corpus
from membench.load_options_or_error import load_options_or_error
from membench.load_questions import load_questions
from membench.metric_means import metric_means
from membench.run_track_r import run_track_r
from membench.validate_run_paths import validate_run_paths
from membench.write_run import write_run


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
    run.add_argument(
        "--adapter-options", type=Path, default=None, help="JSON object of options for the adapter"
    )
    args = parser.parse_args(argv)

    options, options_error = load_options_or_error(args.adapter_options)
    if options_error is not None:
        print(options_error, file=sys.stderr)
        return 2

    paths_error = validate_run_paths(args)
    if paths_error is not None:
        print(paths_error, file=sys.stderr)
        return 2

    if args.adapter not in ADAPTERS:
        print(
            f"unknown adapter: {args.adapter}; known: {', '.join(sorted(ADAPTERS))}",
            file=sys.stderr,
        )
        return 2

    workspace = args.out / "workspace"
    try:
        inspect.signature(ADAPTERS[args.adapter]).bind(workspace, **options)
    except TypeError as error:
        print(f"rejected adapter option: {error}", file=sys.stderr)
        return 2

    workspace.mkdir(parents=True, exist_ok=True)
    adapter = build_adapter(args.adapter, workspace, options)
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
        adapter_options=options,
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
