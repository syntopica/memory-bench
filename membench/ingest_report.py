"""What ingesting a corpus cost a memory system."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IngestReport:
    """Measured cost of one ingestion.

    Token counts are counted, never priced: a monetary estimate is derived
    later and reported separately.

    Attributes:
        seconds: Wall-clock duration of the ingestion.
        persisted_bytes: Total bytes the system persists after ingesting, as
            measured on disk. This is not derived-index size: it includes any
            copy of the corpus the system keeps, and FTS5's content table keeps
            one verbatim. Separating derived storage from a retained copy needs
            a boundary defined across several systems, which this phase does
            not have.
        input_tokens: Model input tokens the ingestion consumed, zero if none.
        output_tokens: Model output tokens the ingestion consumed, zero if none.
    """

    seconds: float
    persisted_bytes: int
    input_tokens: int
    output_tokens: int
