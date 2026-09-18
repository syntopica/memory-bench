"""Read a run's adapter options, or explain why they cannot be read."""

from pathlib import Path

from membench.load_adapter_options import load_adapter_options


def load_options_or_error(
    adapter_options: Path | None,
) -> tuple[dict[str, object], str | None]:
    """Return the parsed adapter options, or an error message instead.

    Args:
        adapter_options: The `--adapter-options` path, or None.

    Returns:
        A pair of the parsed options (empty on failure) and either None, or a
        message explaining why the options could not be read.
    """
    if adapter_options is not None and not adapter_options.exists():
        return {}, f"adapter options not found: {adapter_options}"
    try:
        return load_adapter_options(adapter_options), None
    except ValueError as error:
        return {}, str(error)
