import json
from pathlib import Path

import pytest

from membench.build_adapter import ADAPTERS
from membench.cli import main
from membench.ingest_report import IngestReport

FIXTURE = Path(__file__).resolve().parent.parent / "corpora" / "fixture"


def test_a_baseline_run_over_the_fixture_produces_scores(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = main(
        [
            "run",
            "--adapter",
            "baseline_fts5",
            "--corpus",
            str(FIXTURE / "corpus.jsonl"),
            "--questions",
            str(FIXTURE / "questions.jsonl"),
            "--out",
            str(out),
        ]
    )
    assert exit_code == 0
    lines = (out / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6
    recalls = [json.loads(line)["recall_at_10"] for line in lines]
    assert sum(recalls) > 0
    assert (out / "workspace" / "index.db").exists()


def test_an_unknown_adapter_is_refused(tmp_path: Path):
    exit_code = main(
        [
            "run",
            "--adapter",
            "nope",
            "--corpus",
            str(FIXTURE / "corpus.jsonl"),
            "--questions",
            str(FIXTURE / "questions.jsonl"),
            "--out",
            str(tmp_path / "run"),
        ]
    )
    assert exit_code == 2


def _run(out: Path, **overrides: str) -> int:
    args = {
        "--adapter": "baseline_fts5",
        "--corpus": str(FIXTURE / "corpus.jsonl"),
        "--questions": str(FIXTURE / "questions.jsonl"),
        "--out": str(out),
    }
    args.update(overrides)
    argv = ["run"]
    for flag, value in args.items():
        argv.extend([flag, value])
    return main(argv)


def test_a_zero_k_is_refused_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--k": "0"})
    assert exit_code == 2
    assert not out.exists()


def test_a_negative_k_is_refused_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--k": "-3"})
    assert exit_code == 2
    assert not out.exists()


def test_a_missing_corpus_is_refused_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--corpus": str(FIXTURE / "no-such-corpus.jsonl")})
    assert exit_code == 2
    assert not out.exists()


def test_a_missing_questions_file_is_refused_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--questions": str(FIXTURE / "no-such-questions.jsonl")})
    assert exit_code == 2
    assert not out.exists()


def test_a_second_run_into_the_same_directory_is_refused(tmp_path: Path):
    out = tmp_path / "run"
    assert _run(out) == 0
    (out / "unrelated.txt").write_text("keep me", encoding="utf-8")
    manifest_before = (out / "manifest.json").read_text(encoding="utf-8")

    exit_code = _run(out)

    assert exit_code == 2
    assert (out / "manifest.json").read_text(encoding="utf-8") == manifest_before
    assert (out / "unrelated.txt").read_text(encoding="utf-8") == "keep me"


def test_force_permits_overwriting_a_previous_run(tmp_path: Path):
    out = tmp_path / "run"
    assert _run(out) == 0
    (out / "unrelated.txt").write_text("keep me", encoding="utf-8")

    exit_code = main(
        [
            "run",
            "--adapter",
            "baseline_fts5",
            "--corpus",
            str(FIXTURE / "corpus.jsonl"),
            "--questions",
            str(FIXTURE / "questions.jsonl"),
            "--out",
            str(out),
            "--force",
        ]
    )

    assert exit_code == 0
    assert (out / "unrelated.txt").read_text(encoding="utf-8") == "keep me"


def test_a_shallow_k_publishes_no_number_under_a_deeper_name(tmp_path: Path):
    out = tmp_path / "run"
    assert _run(out, **{"--k": "2"}) == 0
    rows = [
        json.loads(line) for line in (out / "raw.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert all(row["depth"] == 2 for row in rows)
    assert all(row["recall_at_5"] is None for row in rows)
    assert all(row["recall_at_10"] is None for row in rows)
    assert all(isinstance(row["recall_at_1"], float) for row in rows)


def test_the_run_reports_its_means_and_what_it_excluded(tmp_path: Path, capsys):
    assert _run(tmp_path / "run") == 0
    printed = capsys.readouterr().out
    assert "recall_at_1@k=10:" in printed
    assert "0 excluded as not applicable to Track R" in printed


def test_a_metric_the_run_never_observed_is_reported_as_unavailable(tmp_path: Path, capsys):
    assert _run(tmp_path / "run", **{"--k": "2"}) == 0
    printed = capsys.readouterr().out
    assert "recall_at_10@k=2: n/a" in printed


def test_missing_adapter_options_file_exits_2_and_writes_nothing(tmp_path: Path):
    out = tmp_path / "run"
    exit_code = _run(out, **{"--adapter-options": str(tmp_path / "no-such-options.json")})
    assert exit_code == 2
    assert not out.exists()


def test_a_non_object_adapter_options_file_exits_2_and_writes_nothing(tmp_path: Path):
    options = tmp_path / "options.json"
    options.write_text("[1, 2]", encoding="utf-8")
    out = tmp_path / "run"
    exit_code = _run(out, **{"--adapter-options": str(options)})
    assert exit_code == 2
    assert not out.exists()


def test_an_unknown_option_exits_2_and_writes_nothing(tmp_path: Path):
    options = tmp_path / "options.json"
    options.write_text('{"nope": 1}', encoding="utf-8")
    out = tmp_path / "run"
    code = main(
        [
            "run",
            "--adapter",
            "baseline_fts5",
            "--corpus",
            str(FIXTURE / "corpus.jsonl"),
            "--questions",
            str(FIXTURE / "questions.jsonl"),
            "--out",
            str(out),
            "--adapter-options",
            str(options),
        ]
    )
    assert code == 2
    assert not out.exists()


def test_an_unknown_adapters_message_is_printed_to_stderr(tmp_path: Path, capsys):
    """A test that only checks the exit code cannot see a message printed to
    the wrong stream.
    """
    exit_code = _run(tmp_path / "run", **{"--adapter": "nope"})
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "unknown adapter: nope" in captured.err
    assert captured.out == ""


class _MisconfiguredAdapter:
    """A stand-in for an adapter that validates its own configuration."""

    def __init__(self, workspace: Path) -> None:
        raise KeyError("gateway_url")


def test_an_adapters_own_key_error_is_not_reported_as_an_unknown_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setitem(ADAPTERS, "misconfigured", _MisconfiguredAdapter)
    with pytest.raises(KeyError, match="gateway_url"):
        _run(tmp_path / "run", **{"--adapter": "misconfigured"})


class _StrictAdapter:
    """A stand-in for an adapter that rejects one of its own option's values."""

    def __init__(self, workspace: Path, url: str = "") -> None:
        if not url:
            raise TypeError("url must not be empty")


def test_an_adapters_own_type_error_is_not_reported_as_a_rejected_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setitem(ADAPTERS, "strict", _StrictAdapter)
    options = tmp_path / "options.json"
    options.write_text('{"url": ""}', encoding="utf-8")
    with pytest.raises(TypeError, match="url must not be empty"):
        _run(tmp_path / "run", **{"--adapter": "strict", "--adapter-options": str(options)})


class _NoticingAdapter:
    """A stand-in that records whether its workspace already existed."""

    workspace_existed_at_construction: bool = False

    def __init__(self, workspace: Path) -> None:
        type(self).workspace_existed_at_construction = workspace.exists()

    def setup(self) -> None:
        pass

    def ingest(self, corpus: object) -> IngestReport:
        return IngestReport(seconds=0.0, persisted_bytes=0, input_tokens=0, output_tokens=0)

    def query(self, question: str, k: int, token_budget: int | None) -> list:
        return []

    def teardown(self) -> None:
        pass


def test_the_workspace_exists_before_the_adapter_is_constructed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setitem(ADAPTERS, "noticing", _NoticingAdapter)
    exit_code = _run(tmp_path / "run", **{"--adapter": "noticing"})
    assert exit_code == 0
    assert _NoticingAdapter.workspace_existed_at_construction is True


class _ProbeAdapter:
    """A stand-in that accepts and discards whatever options it is given.

    It exists only to let a test drive the real CLI end to end with options a
    shipped adapter does not accept, so the manifest's verbatim guarantee is
    checked across the whole path, not only at the `build_manifest` unit.
    """

    def __init__(self, workspace: Path, **options: object) -> None:
        del workspace, options

    def setup(self) -> None:
        pass

    def ingest(self, corpus: object) -> IngestReport:
        del corpus
        return IngestReport(seconds=0.0, persisted_bytes=0, input_tokens=0, output_tokens=0)

    def query(self, question: str, k: int, token_budget: int | None) -> list:
        del question, k, token_budget
        return []

    def teardown(self) -> None:
        pass


def test_the_written_manifest_carries_the_cli_s_options_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setitem(ADAPTERS, "probe", _ProbeAdapter)
    given_options = {"seed": 7, "gateway": {"timeout_ms": 500, "retries": None}, "label": "café"}
    options_path = tmp_path / "options.json"
    options_path.write_text(json.dumps(given_options), encoding="utf-8")
    out = tmp_path / "run"

    exit_code = _run(out, **{"--adapter": "probe", "--adapter-options": str(options_path)})

    assert exit_code == 0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["adapter_options"] == given_options
