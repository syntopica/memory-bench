from membench.redact_remote_url import redact_remote_url


def test_a_token_in_an_https_remote_is_removed():
    assert (
        redact_remote_url("https://user:secret@github.com/owner/repo.git")
        == "https://github.com/owner/repo.git"
    )


def test_a_plain_https_remote_is_unchanged():
    assert (
        redact_remote_url("https://github.com/owner/repo.git")
        == "https://github.com/owner/repo.git"
    )


def test_an_scp_style_remote_is_unchanged():
    assert redact_remote_url("git@github.com:owner/repo.git") == "git@github.com:owner/repo.git"
