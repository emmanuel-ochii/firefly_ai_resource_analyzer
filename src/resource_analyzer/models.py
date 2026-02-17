"""Datamodels for resource analyzer output."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Literal

State = Literal["Missing", "Match", "Modified"]

def model_dataclass() -> Any:
    """Return a dataclass decorator with safe slots handling.

    Python 3.10+ supports ``slots=True`` in ``dataclass``.
    For older runtimes (e.g. 3.9), fallback to a regular dataclass so
    class creation does not fail if compatibility is required later.
    """

    if sys.version_info >= (3, 10):
        return dataclass(slots=True)
    return dataclass()


@model_dataclass()
class ChangeLogEntry:
    """Represents one field-level difference between cloud and IaC resources."""

    keyName: str
    cloudValue: Any
    iacValue: Any

    def to_dict(self) -> dict[str, Any]:
        """Serialize the changelog entry to a JSON-compatible dictionary."""
        return {
            "KeyName": self.keyName,
            "CloudValue": self.cloudValue,
            "IacValue": self.iacValue,
        }


@model_dataclass()
class ReportItem:
    """Comparison result for one cloud resource."""

    cloudResourceItem: dict[str, Any]
    iacResourceItem: dict[str, Any] | None
    state: State
    changeLog: list[ChangeLogEntry]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report item to a JSON-compatible dictionary."""
        return {
            "CloudResourceItem": self.cloudResourceItem,
            "IacResourceItem": self.iacResourceItem,
            "State": self.state,
            "ChangeLog": [entry.to_dict() for entry in self.changeLog],
        }


@model_dataclass()
class ResourceReport:
    """Top-level report output."""

    generatedAt: str
    matchKeyUsed: str
    totalResources: int
    items: list[ReportItem]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete report to a JSON-compatible dictionary."""
        return {
            "GeneratedAt": self.generatedAt,
            "MatchKeyUsed": self.matchKeyUsed,
            "TotalResources": self.totalResources,
            "Resources": [item.to_dict() for item in self.items],
        }
