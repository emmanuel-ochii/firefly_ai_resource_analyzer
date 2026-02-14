"""Tests for matching and deep diff behavior."""

from __future__ import annotations

from resource_analyzer.diff import analyze_resources, resolve_match_key


def test_missing_when_cloud_resource_has_no_iac_match() -> None:
    cloud = [{"name": "web-a", "spec": {"replicas": 2}}]
    iac = [{"name": "web-b", "spec": {"replicas": 2}}]

    items = analyze_resources(cloud, iac, match_key="name")

    assert len(items) == 1
    assert items[0].state == "Missing"
    assert items[0].iacResourceItem is None
    assert items[0].changeLog == []


def test_match_when_nested_structures_are_identical() -> None:
    cloud = [
        {
            "id": "r-1",
            "spec": {
                "replicas": 2,
                "containers": [{"name": "api", "image": "api:1.0"}],
            },
        }
    ]
    iac = [
        {
            "id": "r-1",
            "spec": {
                "replicas": 2,
                "containers": [{"name": "api", "image": "api:1.0"}],
            },
        }
    ]

    items = analyze_resources(cloud, iac, match_key="id")

    assert items[0].state == "Match"
    assert items[0].changeLog == []


def test_modified_when_nested_dictionary_value_differs() -> None:
    cloud = [{"name": "svc", "spec": {"replicas": 3, "port": 8080}}]
    iac = [{"name": "svc", "spec": {"replicas": 2, "port": 8080}}]

    items = analyze_resources(cloud, iac, match_key="name")

    assert items[0].state == "Modified"
    assert len(items[0].changeLog) == 1
    diff = items[0].changeLog[0]
    assert diff.keyName == "spec.replicas"
    assert diff.cloudValue == 3
    assert diff.iacValue == 2


def test_modified_when_list_item_differs() -> None:
    cloud = [
        {
            "name": "svc",
            "spec": {"containers": [{"name": "api", "image": "api:2.0"}]},
        }
    ]
    iac = [
        {
            "name": "svc",
            "spec": {"containers": [{"name": "api", "image": "api:1.0"}]},
        }
    ]

    items = analyze_resources(cloud, iac, match_key="name")

    assert items[0].state == "Modified"
    assert len(items[0].changeLog) == 1
    diff = items[0].changeLog[0]
    assert diff.keyName == "spec.containers[0].image"
    assert diff.cloudValue == "api:2.0"
    assert diff.iacValue == "api:1.0"


def test_modified_when_key_is_missing_in_cloud() -> None:
    cloud = [{"name": "bucket-a", "tags": {}}]
    iac = [{"name": "bucket-a", "tags": {"owner": "platform"}}]

    items = analyze_resources(cloud, iac, match_key="name")

    assert items[0].state == "Modified"
    assert len(items[0].changeLog) == 1
    diff = items[0].changeLog[0]
    assert diff.keyName == "tags.owner"
    assert diff.cloudValue is None
    assert diff.iacValue == "platform"


def test_auto_detect_match_key_prefers_configured_order() -> None:
    cloud = [{"name": "a", "id": "1"}]
    iac = [{"name": "a", "id": "1"}]

    match_key = resolve_match_key(cloud, iac, requested_key=None)

    assert match_key == "id"
