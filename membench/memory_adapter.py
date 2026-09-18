"""The contract every memory system under test implements."""

from collections.abc import Sequence
from typing import Protocol

from membench.conversation import Conversation
from membench.evidence import Evidence
from membench.ingest_report import IngestReport

ADAPTER_CONTRACT_VERSION = "2.0"
"""Version of the `MemoryAdapter` contract below.

The Protocol is published: adapters for systems this repository does not own
are written against it, and a run has to say which shape of adapter produced
it. The major part is raised by any change that breaks an existing adapter -
a new method, a changed signature, a changed meaning of a returned field - and
the minor part by an addition an existing adapter can ignore.

2.0 adds the token_budget parameter to query.
"""


class MemoryAdapter(Protocol):
    """A memory system, as the harness sees it."""

    def setup(self) -> None:
        """Bring the system up, empty, ready to ingest."""
        ...

    def ingest(self, corpus: Sequence[Conversation]) -> IngestReport:
        """Ingest the corpus chronologically and report what it cost."""
        ...

    def query(self, question: str, k: int, token_budget: int | None) -> list[Evidence]:
        """Return at most k pieces of evidence, best first.

        `token_budget` is the harness's `count_tokens` applied to the returned
        texts, and it is identical for every system in a run: an adapter
        returns the longest prefix of its ranking that fits, dropping from the
        end. None means unbounded, which is what Track R passes, because Track
        R scores which conversations were found rather than how much text
        came back.
        """
        ...

    def teardown(self) -> None:
        """Release every resource the system holds."""
        ...
