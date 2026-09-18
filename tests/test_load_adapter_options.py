from pathlib import Path

import pytest

from membench.load_adapter_options import load_adapter_options


def test_no_path_is_no_options():
    assert load_adapter_options(None) == {}


def test_it_reads_a_json_object(tmp_path: Path):
    path = tmp_path / "options.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    assert load_adapter_options(path) == {"a": 1}


def test_a_json_array_is_refused(tmp_path: Path):
    path = tmp_path / "options.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_adapter_options(path)
