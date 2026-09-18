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

Construction is part of the contract but outside the Protocol below, because
it is where adapters differ: an adapter is a callable that takes a workspace
`Path` it owns exclusively, plus keyword options recorded verbatim in the
run's manifest, and it creates nothing outside that workspace. The harness
creates the workspace directory before constructing the adapter, so `__init__`
and `setup()` may assume it exists; the harness itself never writes inside
it - a run's frozen artifacts (`manifest.json`, `raw.jsonl`) land in the
workspace's parent directory instead, so an adapter's own files never collide
with them. Options must be JSON-representable: they are read from a JSON file
and recorded verbatim in the manifest, so a value that cannot round-trip
through JSON cannot be reproduced from that record. `build_adapter` is where a
name is turned into one of these callables.
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
        end. Dropping is from the end only - never from the middle, and never
        by re-ranking to pack the budget better, because a system that repacks
        is answering a different question from one that does not.

        None means unbounded, which is what Track R passes, because Track R
        scores which conversations were found rather than how much text came
        back. Otherwise the budget is zero or greater; a negative budget is a
        caller error, and an adapter is not required to detect one. A piece of
        evidence whose text is empty costs nothing, so a budget of zero admits
        it - "zero tokens" bounds the text returned, not the number of hits.
        """
        ...

    def teardown(self) -> None:
        """Release every resource the system holds."""
        ...
