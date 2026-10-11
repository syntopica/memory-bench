import subprocess
from pathlib import Path

from membench.file_source import file_source

FIXTURE_CORPUS = Path(__file__).resolve().parent.parent / "corpora" / "fixture" / "corpus.jsonl"


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _repository_with_corpus(root: Path) -> Path:
    _git(root, "init", "-q")
    _git(root, "remote", "add", "origin", "https://user:token@example.invalid/corpora.git")
    corpus = root / "data" / "corpus.jsonl"
    corpus.parent.mkdir()
    corpus.write_text("{}\n", encoding="utf-8")
    _git(root, "add", "data/corpus.jsonl")
    _git(root, "commit", "-q", "-m", "corpus")
    return corpus


def test_a_committed_file_names_its_repository_and_commit(tmp_path: Path):
    corpus = _repository_with_corpus(tmp_path)

    source = file_source(corpus)

    assert source == {
        "repository": "https://example.invalid/corpora.git",
        "commit": _git(tmp_path, "rev-parse", "HEAD"),
    }


def test_a_modified_file_has_no_commit(tmp_path: Path):
    corpus = _repository_with_corpus(tmp_path)
    corpus.write_text('{"changed": true}\n', encoding="utf-8")

    assert file_source(corpus)["commit"] is None


def test_an_untracked_file_has_no_commit(tmp_path: Path):
    _repository_with_corpus(tmp_path)
    loose = tmp_path / "data" / "loose.jsonl"
    loose.write_text("{}\n", encoding="utf-8")

    assert file_source(loose)["commit"] is None


def test_a_repository_without_origin_has_no_repository(tmp_path: Path):
    corpus = _repository_with_corpus(tmp_path)
    _git(tmp_path, "remote", "remove", "origin")

    source = file_source(corpus)

    assert source["repository"] is None
    assert source["commit"] is not None


def test_a_file_in_no_repository_has_no_source(tmp_path: Path):
    loose = tmp_path / "corpus.jsonl"
    loose.write_text("{}\n", encoding="utf-8")

    assert file_source(loose) == {"repository": None, "commit": None}


def test_the_shipped_fixture_has_a_repository():
    assert file_source(FIXTURE_CORPUS)["repository"]
