"""Read the options a run passes to its adapter's constructor."""

import json
from pathlib import Path


def load_adapter_options(path: Path | None) -> dict[str, object]:
    """Return the adapter options recorded at `path`.

    Args:
        path: A JSON file holding one object, or None.

    Returns:
        The parsed object, or `{}` when `path` is None.

    Raises:
        ValueError: The file's content is not valid JSON, or does not parse to
            a JSON object.
    """
    if path is None:
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"adapter options file is not valid JSON: {path}: {error}") from error
    if not isinstance(parsed, dict):
        raise ValueError(f"adapter options must be a JSON object: {path}")
    return parsed
