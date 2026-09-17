from pathlib import Path

from membench.sha256_file import sha256_file


def test_hashes_the_bytes_of_the_file(tmp_path: Path):
    path = tmp_path / "a.txt"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_the_same_content_hashes_the_same(tmp_path: Path):
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_bytes(b"same")
    second.write_bytes(b"same")
    assert sha256_file(first) == sha256_file(second)
