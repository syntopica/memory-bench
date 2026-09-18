"""Guarantee that a system under test is torn down, however the run ends."""

import sys
from collections.abc import Iterator
from contextlib import contextmanager

from membench.memory_adapter import MemoryAdapter


@contextmanager
def adapter_lifecycle(adapter: MemoryAdapter) -> Iterator[MemoryAdapter]:
    """Run a block and call `adapter.teardown()` whether or not it succeeded.

    For the FTS5 baseline a leaked adapter is a SQLite handle the interpreter
    closes anyway. For the systems this contract exists to admit it is a
    server, a container or a remote index, and a run that fails during ingest
    would otherwise leave it running with nothing holding a reference to it.

    A teardown that fails while the block is already failing is reported on
    stderr rather than raised: the exception that ended the run is the one an
    operator has to debug, and a cleanup error that replaced it would send
    them after the wrong cause. On the success path there is nothing to mask,
    so a failing teardown raises - a run whose system did not release its
    resources has not finished cleanly and must not be reported as if it had.

    Args:
        adapter: The system under test, already constructed.

    Yields:
        The same adapter, for the block to set up, ingest and query.
    """
    try:
        yield adapter
    except BaseException:
        try:
            adapter.teardown()
        except Exception as teardown_error:
            print(
                f"teardown failed after the run already failed: {teardown_error}", file=sys.stderr
            )
        raise
    else:
        adapter.teardown()
