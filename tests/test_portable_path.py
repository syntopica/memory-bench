from pathlib import Path

from membench.portable_path import portable_path


def test_a_file_under_the_working_directory_is_named_relatively(tmp_path: Path, monkeypatch):
    target = tmp_path / "corpora" / "fixture" / "corpus.jsonl"
    target.parent.mkdir(parents=True)
    target.touch()
    monkeypatch.chdir(tmp_path)
    assert portable_path(target) == "corpora/fixture/corpus.jsonl"


def test_a_file_outside_the_working_directory_keeps_only_its_name(tmp_path: Path, monkeypatch):
    outside = tmp_path / "elsewhere" / "corpus.jsonl"
    outside.parent.mkdir(parents=True)
    outside.touch()
    inside = tmp_path / "run"
    inside.mkdir()
    monkeypatch.chdir(inside)
    assert portable_path(outside) == "corpus.jsonl"


def test_an_absolute_home_path_never_survives_into_the_label(tmp_path: Path, monkeypatch):
    target = tmp_path / "corpus.jsonl"
    target.touch()
    monkeypatch.chdir(tmp_path)
    assert portable_path(target.resolve()) == "corpus.jsonl"


def test_a_file_in_a_repository_is_named_from_its_root_whatever_the_working_directory(
    tmp_path: Path, monkeypatch
):
    (tmp_path / ".git").mkdir()
    target = tmp_path / "corpora" / "fixture" / "corpus.jsonl"
    target.parent.mkdir(parents=True)
    target.touch()
    monkeypatch.chdir(target.parent)
    assert portable_path(target) == "corpora/fixture/corpus.jsonl"


def test_a_repository_outside_the_working_directory_still_names_the_file_from_its_root(
    tmp_path: Path, monkeypatch
):
    repository = tmp_path / "corpus-repo"
    (repository / ".git").mkdir(parents=True)
    target = repository / "spanish" / "corpus.jsonl"
    target.parent.mkdir()
    target.touch()
    elsewhere = tmp_path / "run"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert portable_path(target) == "spanish/corpus.jsonl"
