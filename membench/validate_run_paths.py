"""Reject a run whose corpus, questions, k or output directory disqualify it."""

import argparse


def validate_run_paths(args: argparse.Namespace) -> str | None:
    """Return why this run must be refused, or None when it may proceed.

    Args:
        args: The parsed `run` subcommand arguments.

    Returns:
        None when the run may proceed, or a message to print to stderr.
    """
    if args.k < 1:
        return f"--k must be at least 1, got {args.k}"
    if not args.corpus.exists():
        return f"corpus not found: {args.corpus}"
    if not args.questions.exists():
        return f"questions not found: {args.questions}"
    manifest_path = args.out / "manifest.json"
    if manifest_path.exists() and not args.force:
        return f"refusing to overwrite an existing run: {manifest_path} (use --force)"
    return None
