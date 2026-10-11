"""Strip credentials from a git remote before a manifest publishes it."""

from urllib.parse import urlsplit, urlunsplit


def redact_remote_url(url: str) -> str:
    """Return `url` without any user name or password in its authority.

    An HTTPS remote can carry a token as `https://<token>@host/...`, and a
    manifest is published, so the user-information part is dropped from every
    URL that has a scheme. An scp-style remote (`git@host:owner/repo.git`) has
    no scheme and no secret: its `git@` names the protocol's account, and it is
    returned as it is.

    Args:
        url: The remote as `git remote get-url` printed it.

    Returns:
        The same remote with no credentials in it.
    """
    parts = urlsplit(url)
    if not parts.scheme or "@" not in parts.netloc:
        return url
    host = parts.netloc.rsplit("@", 1)[1]
    return urlunsplit(parts._replace(netloc=host))
