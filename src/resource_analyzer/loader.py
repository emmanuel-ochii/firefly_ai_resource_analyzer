"""Input loading helpers for resource analyzer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RESOURCE_CONTAINER_KEYS: tuple[str, ...] = ("resources", "items", "data")


class LoaderError(ValueError):
    """Raised when input JSON cannot be loaded or normalized."""


def load_json_file(path: str | Path) -> Any:
    """Load and parse a JSON file.

    Args:
        path: File system path to a JSON file.

    Returns:
        Parsed JSON payload.

    Raises:
        LoaderError: If file cannot be read or parsed.
    """

    file_path = Path(path)
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise LoaderError(f"JSON file not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise LoaderError(
            "Invalid JSON in "
            f"{file_path}: {exc.msg} (line {exc.lineno}, column {exc.colno})"
        ) from exc


def extract_resources(payload: Any, source_name: str) -> list[dict[str, Any]]:
    """Extract the resource list from supported JSON shapes.

    Supported shapes:
    - top-level list of resource objects
    - top-level object containing list under one of: resources, items, data

    Args:
        payload: Parsed JSON payload.
        source_name: Human-readable source label for error messages.

    Returns:
        A normalized list of resource dictionaries.

    Raises:
        LoaderError: If payload does not contain a valid resource list.
    """

    if isinstance(payload, list):
        return _validate_resource_list(payload, source_name, "top-level list")

    if isinstance(payload, dict):
        for key in RESOURCE_CONTAINER_KEYS:
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return _validate_resource_list(
                    candidate, source_name, f"object['{key}']"
                )

        supported = ", ".join(RESOURCE_CONTAINER_KEYS)
        raise LoaderError(
            f"Could not find a resource list in {source_name}. "
            f"Expected a top-level list or an object with one of: {supported}."
        )

    raise LoaderError(
        f"Unsupported JSON structure in {source_name}. "
        f"Expected list or object, got {type(payload).__name__}."
    )


def _validate_resource_list(
    resources: list[Any], source_name: str, context: str
) -> list[dict[str, Any]]:
    """Ensure the extracted list contains only JSON objects."""

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(resources):
        if not isinstance(item, dict):
            raise LoaderError(
                f"Invalid resource at index {index} in {source_name} ({context}). "
                f"Expected object, got {type(item).__name__}."
            )
        normalized.append(item)
    return normalized
