"""Datamodels for resource analyzer output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

State = Literal["Missing", "Match", "Modified"]


@dataclass(slots=True)
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


@dataclass(slots=True)
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


@dataclass(slots=True)
class ResourceReport:
    """Top-level report output."""

    generatedAt: str
    matchKeyUsed: str
    items: list[ReportItem]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete report to a JSON-compatible dictionary."""
        return {
            "GeneratedAt": self.generatedAt,
            "MatchKeyUsed": self.matchKeyUsed,
            "Items": [item.to_dict() for item in self.items],
        }
