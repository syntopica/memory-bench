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

2.0 adds the token_budget parameter to query, and changes what an adapter is
constructed with: 1.0 handed it `<out>/index.db`, a SQLite file it was to
create, and 2.0 hands it `<out>/workspace`, a directory it owns. That half is
the more dangerous one, because it breaks quietly. A 1.0 adapter's signature
still binds, so nothing is refused: it creates its database at the directory
path and fails somewhere else, or not at all. Read this version before
concluding an adapter is broken.

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
        """Return the evidence that answers `question`, best first.

        `k` bounds the **ranked source conversations**, not the pieces of
        evidence. Each distinct conversation id in a hit's `source_ids` spends
        one rank slot, in the order given, deduplicated across the whole
        ranking; a hit that cites nothing spends one slot too; and everything
        past the k-th slot is discarded before scoring. So attaching N
        conversations to one memory costs N of the k, and returning fewer
        hits than k does not mean the ranking fit.

        For a system that consolidates memories this is the rule that matters:
        cite the conversations that actually support the memory, best first. A
        shotgun citation buys nothing - a repeated id is deduplicated to its
        best slot - and it can push the conversation that really answers the
        question out of the budget entirely. Two honest hits can overflow a
        `k` of three if the first names three conversations.

        Source ids are matched **verbatim** against the corpus
        `conversation_id`. Exactly one leading `synthesis/` is forgiven, for
        systems that namespace their derived records; nothing else is
        normalised - not case, not surrounding whitespace, not any other
        namespace or prefix. An id that does not equal a corpus
        `conversation_id` after that one removal simply never matches, and the
        system is scored the miss.

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
        """Release every resource the system holds.

        The harness guarantees this is called once, whether the run finished
        or an exception ended it part-way through setup, ingest or querying:
        an adapter that holds a server, a container or a remote index can rely
        on getting the chance to release it. It may therefore be called on a
        system that was never fully set up, so it has to tolerate a partial
        state rather than assume its own invariants.

        Raising from here after the run already failed does not mask that
        failure - the harness reports the teardown error and re-raises the
        original - but on a run that otherwise succeeded a failure here fails
        the run.
        """
        ...
