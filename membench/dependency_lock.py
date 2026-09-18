"""Identify the dependency lock a run was built against, or admit it is gone."""

from pathlib import Path

from membench.sha256_file import sha256_file

_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def dependency_lock() -> dict[str, str]:
    """Return `uv.lock`'s identity, or admit that it is not present.

    The lock is resolved relative to this package's parent, not the working
    directory, because an installed wheel has no lock file beside it. The
    digest is taken from the lock file on disk at the moment the run happens,
    so an environment installed from a stale lock still records the lock
    currently sitting there, not necessarily the one its packages were
    actually built against.

    Returns:
        `{"path": "uv.lock", "sha256": <digest>}`, or `{"path": "uv.lock",
        "sha256": "unknown"}` when the lock file is absent.
    """
    lock_path = _REPOSITORY_ROOT / "uv.lock"
    if not lock_path.is_file():
        return {"path": "uv.lock", "sha256": "unknown"}
    return {"path": "uv.lock", "sha256": sha256_file(lock_path)}
