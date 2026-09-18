"""Identify the harness commit and working-tree state behind a run."""

import subprocess
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
_UNKNOWN: dict[str, str | bool] = {"commit": "unknown", "dirty": True}


def harness_commit() -> dict[str, str | bool]:
    """Return this harness's own commit and whether its tree was dirty.

    Both git calls run with the package's own root as `cwd`, not the working
    directory a run happens to be launched from: a run started from another
    checkout must still report this harness's commit, not the caller's. A
    manifest that cannot be written is worse than one that admits it does not
    know, so no git failure propagates out of here: any `OSError` from trying
    to run `git` (missing from `PATH`, present but not executable, or any
    other reason it cannot be started), a non-zero return code and empty
    output are all the unknown case.

    Returns:
        `{"commit": "<40 hex chars>", "dirty": bool}`, or
        `{"commit": "unknown", "dirty": True}` when the commit cannot be
        determined.
    """
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return dict(_UNKNOWN)
    commit = revision.stdout.strip()
    if revision.returncode != 0 or not commit:
        return dict(_UNKNOWN)
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=_REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return dict(_UNKNOWN)
    dirty = status.returncode != 0 or bool(status.stdout.strip())
    return {"commit": commit, "dirty": dirty}
