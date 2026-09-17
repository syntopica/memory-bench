from membench.evidence import Evidence
from membench.ingest_report import IngestReport


def test_evidence_carries_text_native_id_and_sources():
    evidence = Evidence(
        text="we are reverting WAL",
        native_id="row-7",
        source_ids=("c1",),
        timestamp="2026-01-05T09:00:00Z",
    )
    assert evidence.text == "we are reverting WAL"
    assert evidence.native_id == "row-7"
    assert evidence.source_ids == ("c1",)


def test_evidence_allows_no_provenance():
    evidence = Evidence(
        text="a consolidated memory", native_id="m-1", source_ids=(), timestamp=None
    )
    assert evidence.source_ids == ()


def test_ingest_report_holds_cost_and_size():
    report = IngestReport(seconds=1.5, persisted_bytes=4096, input_tokens=0, output_tokens=0)
    assert report.seconds == 1.5
    assert report.persisted_bytes == 4096
