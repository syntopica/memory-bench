import pytest

from membench.adapter_lifecycle import adapter_lifecycle


class _Recorder:
    def __init__(self, teardown_error: Exception | None = None) -> None:
        self.torn_down = 0
        self._teardown_error = teardown_error

    def teardown(self) -> None:
        self.torn_down += 1
        if self._teardown_error is not None:
            raise self._teardown_error


def test_a_run_that_finishes_tears_the_adapter_down_once():
    adapter = _Recorder()
    with adapter_lifecycle(adapter):
        pass
    assert adapter.torn_down == 1


def test_a_teardown_failure_on_the_success_path_is_reported():
    adapter = _Recorder(RuntimeError("could not stop the container"))
    with pytest.raises(RuntimeError, match="could not stop the container"), adapter_lifecycle(
        adapter
    ):
        pass


def test_an_ingest_that_raises_still_tears_the_adapter_down():
    adapter = _Recorder()
    with pytest.raises(ValueError, match="corpus is malformed"), adapter_lifecycle(adapter):
        raise ValueError("corpus is malformed")
    assert adapter.torn_down == 1


def test_a_failing_teardown_does_not_mask_the_failure_that_ended_the_run():
    """The order the report has to survive.

    A teardown that raises while the run is already failing would otherwise
    replace the real cause with a cleanup error, and an operator would debug
    the wrong thing. The original propagates; the teardown error is reported
    beside it, not instead of it.
    """
    adapter = _Recorder(RuntimeError("could not stop the container"))
    with pytest.raises(ValueError, match="corpus is malformed"), adapter_lifecycle(adapter):
        raise ValueError("corpus is malformed")
    assert adapter.torn_down == 1


def test_a_failing_teardown_says_so_on_stderr(capsys: pytest.CaptureFixture[str]):
    adapter = _Recorder(RuntimeError("could not stop the container"))
    with pytest.raises(ValueError), adapter_lifecycle(adapter):
        raise ValueError("corpus is malformed")
    assert "could not stop the container" in capsys.readouterr().err
