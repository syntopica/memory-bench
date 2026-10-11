"""Ask git one question about a repository, without letting it fail a run."""

import subprocess
from pathlib import Path


def run_git(arguments: list[str], repository: Path) -> str | None:
    """Return git's stripped standard output, or None when git cannot answer.

    A manifest that cannot be written is worse than one that admits it does
    not know, so nothing here propagates: git missing from `PATH` or not
    executable, and a non-zero exit, are all None. An empty string is an
    answer - `git status --porcelain` on a clean file says exactly that.

    Args:
        arguments: The git subcommand and its arguments, without `git`.
        repository: The directory git runs in.

    Returns:
        The output with surrounding whitespace removed, or None.
    """
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()
