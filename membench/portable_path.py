"""Name a file in a manifest without naming the machine that read it."""

from pathlib import Path

from membench.enclosing_repository_root import enclosing_repository_root


def portable_path(path: Path) -> str:
    """Return a label for `path` that carries no operator-specific directory.

    A manifest is published: `/Users/someone/p/memory-bench/corpora/...` says
    more about whoever ran the benchmark than about the run, and it is wrong
    on every other machine. The digest beside it is the real identity of the
    bytes, so this is only a label, and it is chosen so the same file gets the
    same label wherever the run was launched from: relative to the root of
    the repository that holds the file, when one does; otherwise relative to
    the working directory when the file is inside it; and the bare file name
    when neither applies.

    Args:
        path: The file as the command line named it.

    Returns:
        A POSIX-style relative path, or the file name alone.
    """
    resolved = path.resolve()
    root = enclosing_repository_root(resolved)
    if root is not None:
        return resolved.relative_to(root).as_posix()
    try:
        return resolved.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return resolved.name
