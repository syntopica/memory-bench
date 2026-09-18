from pathlib import Path

import pytest

from membench.adapters.baseline_fts5_adapter import BaselineFts5Adapter
from membench.build_adapter import build_adapter


def test_it_builds_the_baseline_with_its_workspace(tmp_path: Path):
    adapter = build_adapter("baseline_fts5", tmp_path, {})
    assert isinstance(adapter, BaselineFts5Adapter)


def test_an_unknown_adapter_raises(tmp_path: Path):
    with pytest.raises(KeyError):
        build_adapter("nope", tmp_path, {})


def test_an_unrecognised_option_raises_rather_than_being_ignored(tmp_path: Path):
    """A silently ignored option makes the manifest describe a run that did
    not happen.
    """
    with pytest.raises(TypeError):
        build_adapter("baseline_fts5", tmp_path, {"temperature": 0.7})
