"""What ingesting a corpus cost a memory system."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IngestReport:
    """Measured cost of one ingestion.

    Token counts are counted, never priced: a monetary estimate is derived
    later and reported separately.

    Attributes:
        seconds: Wall-clock duration of the ingestion.
        index_bytes: Bytes of derived index the ingestion produced.
        input_tokens: Model input tokens the ingestion consumed, zero if none.
        output_tokens: Model output tokens the ingestion consumed, zero if none.
    """

    seconds: float
    index_bytes: int
    input_tokens: int
    output_tokens: int
