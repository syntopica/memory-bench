"""Hash a file's bytes, so a manifest pins content rather than a path."""

import hashlib
from pathlib import Path

_CHUNK = 1 << 20


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 of a file's bytes.

    Args:
        path: The file to hash.

    Returns:
        The 64-character hex digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()
