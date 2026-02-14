"""Tests for JSON loading and resource extraction."""

from __future__ import annotations

import pytest

from resource_analyzer.loader import LoaderError, extract_resources


def test_extract_resources_from_top_level_list() -> None:
    payload = [{"name": "a"}, {"name": "b"}]

    resources = extract_resources(payload, source_name="cloud.json")

    assert resources == payload


def test_extract_resources_from_object_container() -> None:
    payload = {"resources": [{"id": "1"}, {"id": "2"}]}

    resources = extract_resources(payload, source_name="iac.json")

    assert resources == payload["resources"]


def test_extract_resources_invalid_shape_raises_error() -> None:
    payload = {"unexpected": [{"id": "1"}]}

    with pytest.raises(LoaderError, match="Could not find a resource list"):
        extract_resources(payload, source_name="iac.json")
