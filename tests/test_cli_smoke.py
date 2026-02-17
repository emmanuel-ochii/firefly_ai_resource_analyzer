"""CLI smoke test using temporary JSON files."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_smoke_generates_report_file(tmp_path: Path) -> None:
    cloud = [{"name": "service-a", "spec": {"replicas": 3}}]
    iac = [{"name": "service-a", "spec": {"replicas": 1}}]

    cloud_path = tmp_path / "cloud.json"
    iac_path = tmp_path / "iac.json"
    report_path = tmp_path / "report.json"

    cloud_path.write_text(json.dumps(cloud), encoding="utf-8")
    iac_path.write_text(json.dumps(iac), encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "resource_analyzer",
            "--cloud",
            str(cloud_path),
            "--iac",
            str(iac_path),
            "--match-key",
            "name",
            "--out",
            str(report_path),
            "--pretty",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert set(payload.keys()) == {"GeneratedAt", "MatchKeyUsed", "TotalResources", "Resources"}
    assert payload["MatchKeyUsed"] == "name"
    assert payload["TotalResources"] == 1
    assert isinstance(payload["Resources"], list)
    assert payload["Resources"][0]["State"] == "Modified"
    assert payload["Resources"][0]["ChangeLog"][0]["KeyName"] == "spec.replicas"


def test_cli_smoke_generates_array_output_format(tmp_path: Path) -> None:
    cloud = [{"name": "service-a", "spec": {"replicas": 3}}]
    iac = [{"name": "service-a", "spec": {"replicas": 1}}]

    cloud_path = tmp_path / "cloud.json"
    iac_path = tmp_path / "iac.json"
    report_path = tmp_path / "report-array.json"

    cloud_path.write_text(json.dumps(cloud), encoding="utf-8")
    iac_path.write_text(json.dumps(iac), encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "resource_analyzer",
            "--cloud",
            str(cloud_path),
            "--iac",
            str(iac_path),
            "--match-key",
            "name",
            "--format",
            "array",
            "--out",
            str(report_path),
            "--pretty",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload[0]["State"] == "Modified"
    assert payload[0]["ChangeLog"][0]["KeyName"] == "spec.replicas"
