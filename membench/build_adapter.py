"""Construct a system under test from its registered name."""

from collections.abc import Callable, Mapping
from pathlib import Path

from membench.adapters.baseline_fts5_adapter import BaselineFts5Adapter
from membench.memory_adapter import MemoryAdapter

ADAPTERS: dict[str, Callable[..., MemoryAdapter]] = {"baseline_fts5": BaselineFts5Adapter}
"""Every adapter this repository can construct, by the name a run names it with."""


def build_adapter(name: str, workspace: Path, options: Mapping[str, object]) -> MemoryAdapter:
    """Construct the named system under test.

    Every adapter is built from a workspace directory it owns and a mapping of
    options recorded verbatim in the run's manifest. An option the adapter does
    not accept raises rather than being ignored: a run whose manifest lists a
    setting that had no effect describes a run that did not happen.

    Args:
        name: A key of `ADAPTERS`.
        workspace: Directory the adapter owns exclusively.
        options: Keyword options forwarded to the adapter's constructor.

    Returns:
        The constructed adapter, not yet set up.

    Raises:
        KeyError: `name` is not a registered adapter.
        TypeError: `options` contains a key the adapter's constructor does not
            accept.
    """
    adapter_type = ADAPTERS[name]
    return adapter_type(workspace, **options)
