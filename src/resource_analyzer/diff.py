"""Matching and deep-diff logic for resource analyzer."""

from __future__ import annotations

from typing import Any, Hashable

from resource_analyzer.models import ChangeLogEntry, ReportItem

IDENTIFIER_PREFERENCE: tuple[str, ...] = ("id", "resourceId", "arn", "name")
_MISSING = object()


class MatchKeyError(ValueError):
    """Raised when a suitable match key cannot be resolved."""


def resolve_match_key(
    cloud_resources: list[dict[str, Any]],
    iac_resources: list[dict[str, Any]],
    requested_key: str | None,
) -> str:
    """Resolve the match key from CLI input or auto-detection.

    Auto-detection chooses the first key from IDENTIFIER_PREFERENCE that exists
    in at least one cloud resource and at least one IaC resource.
    """

    if requested_key:
        if _key_exists_in_dataset(cloud_resources, requested_key) and _key_exists_in_dataset(
            iac_resources, requested_key
        ):
            return requested_key
        raise MatchKeyError(
            f"Match key '{requested_key}' was not found in both datasets. "
            "Provide a key that exists in both cloud and IaC resources."
        )

    for key in IDENTIFIER_PREFERENCE:
        if _key_exists_in_dataset(cloud_resources, key) and _key_exists_in_dataset(
            iac_resources, key
        ):
            return key

    ordered_keys = ", ".join(IDENTIFIER_PREFERENCE)
    raise MatchKeyError(
        "Could not auto-detect a match key. "
        f"Checked: {ordered_keys}. Please provide --match-key."
    )


def analyze_resources(
    cloud_resources: list[dict[str, Any]],
    iac_resources: list[dict[str, Any]],
    match_key: str,
) -> list[ReportItem]:
    """Compare cloud resources against IaC resources.

    Uses an O(n) lookup map for IaC resources by ``match_key``.
    """

    iac_lookup = build_iac_lookup(iac_resources, match_key)
    items: list[ReportItem] = []

    for cloud_item in cloud_resources:
        cloud_key = cloud_item.get(match_key, _MISSING)
        if cloud_key is _MISSING or not _is_hashable(cloud_key):
            items.append(
                ReportItem(
                    cloudResourceItem=cloud_item,
                    iacResourceItem=None,
                    state="Missing",
                    changeLog=[],
                )
            )
            continue

        iac_item = iac_lookup.get(cloud_key)
        if iac_item is None:
            items.append(
                ReportItem(
                    cloudResourceItem=cloud_item,
                    iacResourceItem=None,
                    state="Missing",
                    changeLog=[],
                )
            )
            continue

        change_log = deep_diff(cloud_item, iac_item)
        state = "Match" if not change_log else "Modified"
        items.append(
            ReportItem(
                cloudResourceItem=cloud_item,
                iacResourceItem=iac_item,
                state=state,
                changeLog=change_log,
            )
        )

    return items


def build_iac_lookup(
    iac_resources: list[dict[str, Any]], match_key: str
) -> dict[Hashable, dict[str, Any]]:
    """Build an IaC lookup table for O(1) matching by key value."""

    lookup: dict[Hashable, dict[str, Any]] = {}
    for index, resource in enumerate(iac_resources):
        if match_key not in resource:
            continue

        key_value = resource[match_key]
        if not _is_hashable(key_value):
            raise MatchKeyError(
                f"IaC resource at index {index} has non-hashable match key "
                f"value for '{match_key}': {key_value!r}"
            )

        if key_value in lookup:
            raise MatchKeyError(
                f"Duplicate IaC match key value for '{match_key}': {key_value!r}. "
                "Matching must be unambiguous."
            )

        lookup[key_value] = resource

    return lookup


def deep_diff(cloud_value: Any, iac_value: Any, path: str = "") -> list[ChangeLogEntry]:
    """Deeply compare two JSON-like values and return all differences.

    List ordering matters: list elements are compared by index.
    """

    differences: list[ChangeLogEntry] = []
    _walk_differences(cloud_value, iac_value, path, differences)
    return differences


def _walk_differences(
    cloud_value: Any,
    iac_value: Any,
    path: str,
    differences: list[ChangeLogEntry],
) -> None:
    """Recursively traverse two JSON-like values and collect diffs."""

    if isinstance(cloud_value, dict) and isinstance(iac_value, dict):
        all_keys = sorted(set(cloud_value.keys()) | set(iac_value.keys()))
        for key in all_keys:
            child_path = f"{path}.{key}" if path else key
            cloud_child = cloud_value.get(key, _MISSING)
            iac_child = iac_value.get(key, _MISSING)

            if cloud_child is _MISSING or iac_child is _MISSING:
                differences.append(
                    ChangeLogEntry(
                        keyName=child_path,
                        cloudValue=None if cloud_child is _MISSING else cloud_child,
                        iacValue=None if iac_child is _MISSING else iac_child,
                    )
                )
                continue

            _walk_differences(cloud_child, iac_child, child_path, differences)
        return

    if isinstance(cloud_value, list) and isinstance(iac_value, list):
        max_len = max(len(cloud_value), len(iac_value))
        for index in range(max_len):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            if index >= len(cloud_value):
                differences.append(
                    ChangeLogEntry(
                        keyName=child_path,
                        cloudValue=None,
                        iacValue=iac_value[index],
                    )
                )
                continue
            if index >= len(iac_value):
                differences.append(
                    ChangeLogEntry(
                        keyName=child_path,
                        cloudValue=cloud_value[index],
                        iacValue=None,
                    )
                )
                continue
            _walk_differences(cloud_value[index], iac_value[index], child_path, differences)
        return

    if not _values_equal_strict(cloud_value, iac_value):
        differences.append(
            ChangeLogEntry(
                keyName=path or "$",
                cloudValue=cloud_value,
                iacValue=iac_value,
            )
        )


def _key_exists_in_dataset(resources: list[dict[str, Any]], key: str) -> bool:
    """Check whether key exists in at least one resource object."""

    return any(key in item for item in resources)


def _is_hashable(value: Any) -> bool:
    """Check whether a value can be used as a dictionary key."""

    try:
        hash(value)
    except TypeError:
        return False
    return True


def _values_equal_strict(cloud_value: Any, iac_value: Any) -> bool:
    """Strict comparison: values match only if both type and value match."""

    return type(cloud_value) is type(iac_value) and cloud_value == iac_value
