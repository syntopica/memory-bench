"""Identify the harness commit and working-tree state behind a run."""

import subprocess

_UNKNOWN: dict[str, str | bool] = {"commit": "unknown", "dirty": True}


def harness_commit() -> dict[str, str | bool]:
    """Return the harness commit and whether its tree was dirty.

    A manifest that cannot be written is worse than one that admits it does
    not know, so no git failure propagates out of here: a non-zero return
    code, a missing `git` binary and empty output are all the unknown case.

    Returns:
        `{"commit": "<40 hex chars>", "dirty": bool}`, or
        `{"commit": "unknown", "dirty": True}` when the commit cannot be
        determined.
    """
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return dict(_UNKNOWN)
    commit = revision.stdout.strip()
    if revision.returncode != 0 or not commit:
        return dict(_UNKNOWN)
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return dict(_UNKNOWN)
    dirty = status.returncode != 0 or bool(status.stdout.strip())
    return {"commit": commit, "dirty": dirty}
