"""Empty the adapter workspace a forced re-run is about to hand out again."""

import shutil
from pathlib import Path


def clear_workspace(workspace: Path) -> None:
    """Remove `workspace` and everything in it, if it exists.

    The workspace is `<out>/workspace/`, a directory the harness hands to one
    adapter and nothing else writes into, so a forced re-run removing it
    removes only what a previous run's adapter left there. The contract
    promises ingest into an empty system, and a dirty workspace is the one
    place that promise could break without any flag saying so.

    A symbolic link is unlinked rather than followed: what it points at is not
    this run's workspace, and deleting through it would remove data the
    harness never handed to an adapter.

    Args:
        workspace: The run's `<out>/workspace` directory.
    """
    if workspace.is_symlink():
        workspace.unlink()
    elif workspace.exists():
        shutil.rmtree(workspace)
