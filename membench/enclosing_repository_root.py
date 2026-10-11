"""Find the version-controlled tree a file belongs to."""

from pathlib import Path


def enclosing_repository_root(path: Path) -> Path | None:
    """Return the nearest directory above `path` that holds a `.git` entry.

    A `.git` file counts as well as a directory, because a linked worktree or
    a submodule marks its root with a file pointing at the real repository.
    Only the filesystem is read: no `git` process is started, so a machine
    without git labels a file exactly as one with it does.

    Args:
        path: A resolved, absolute file path.

    Returns:
        The repository root, or None when no ancestor is one.
    """
    for directory in path.parents:
        if (directory / ".git").exists():
            return directory
    return None
