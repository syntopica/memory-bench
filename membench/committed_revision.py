"""Name the commit that holds a file's bytes exactly as they were read."""

from pathlib import Path

from membench.run_git import run_git


def committed_revision(repository: Path, relative_path: str) -> str | None:
    """Return the repository's `HEAD` when it holds this file unmodified.

    A commit is only a source for bytes it contains. A file git does not
    track, or one whose working copy differs from `HEAD`, was read from a tree
    no commit describes, so naming `HEAD` would point a reader at bytes whose
    digest would not match. Those cases, and any git failure, are None.

    Args:
        repository: The root of the repository holding the file.
        relative_path: The file, POSIX-style, relative to that root.

    Returns:
        The 40-character commit, or None when no commit holds these bytes.
    """
    if run_git(["ls-files", "--error-unmatch", "--", relative_path], repository) is None:
        return None
    if run_git(["status", "--porcelain", "--", relative_path], repository) != "":
        return None
    return run_git(["rev-parse", "HEAD"], repository) or None
