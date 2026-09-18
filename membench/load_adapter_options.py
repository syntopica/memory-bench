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
        ValueError: The file's content does not parse as a JSON object.
    """
    if path is None:
        return {}
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"adapter options must be a JSON object: {path}")
    return parsed
