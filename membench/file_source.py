"""Say where a reader can obtain the bytes a manifest's digest verifies."""

from pathlib import Path

from membench.committed_revision import committed_revision
from membench.enclosing_repository_root import enclosing_repository_root
from membench.redact_remote_url import redact_remote_url
from membench.run_git import run_git


def file_source(path: Path) -> dict[str, str | None]:
    """Return the repository and commit a hashed input can be fetched from.

    A `sha256` verifies bytes the reader must already hold; this names where
    to get them. Clone `repository`, check out `commit`, read the manifest's
    `path` - which is relative to that repository's root - and the digest
    beside it must match. The repository is the `origin` remote with any
    credentials removed. Either field is None when it cannot be stated
    honestly: the file is in no repository, the repository has no `origin`,
    or no commit holds the bytes as they were read.

    Recording the remote publishes its URL. A corpus kept in a private
    repository names that repository in every manifest produced from it.

    Args:
        path: The corpus or question file as the command line named it.

    Returns:
        `{"repository": str | None, "commit": str | None}`.
    """
    resolved = path.resolve()
    root = enclosing_repository_root(resolved)
    if root is None:
        return {"repository": None, "commit": None}
    remote = run_git(["remote", "get-url", "origin"], root)
    relative_path = resolved.relative_to(root).as_posix()
    return {
        "repository": redact_remote_url(remote) if remote else None,
        "commit": committed_revision(root, relative_path),
    }
