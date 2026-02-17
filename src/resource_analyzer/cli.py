"""Command-line interface for resource analyzer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from resource_analyzer.diff import MatchKeyError, analyze_resources, resolve_match_key
from resource_analyzer.loader import LoaderError, extract_resources, load_json_file
from resource_analyzer.models import ResourceReport
from resource_analyzer.utils import to_json_text, upload_report_to_s3, utc_now_iso8601


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI parser."""

    parser = argparse.ArgumentParser(
        prog="resource_analyzer",
        description=(
            "Compare cloud resources against IaC resources and emit a JSON resource report."
        ),
    )
    parser.add_argument("--cloud", required=True, help="Path to cloud JSON file")
    parser.add_argument("--iac", required=True, help="Path to IaC JSON file")
    parser.add_argument(
        "--match-key",
        help=(
            "Resource identifier key to match on. "
            "If omitted, auto-detection tries: id, resourceId, arn, name."
        ),
    )
    parser.add_argument("--out", help="Write report JSON to this file path")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )
    parser.add_argument(
        "--format",
        choices=("wrapped", "array"),
        default="wrapped",
        help=(
            "Output format: 'wrapped' includes top-level metadata, "
            "'array' prints only resource comparison entries."
        ),
    )

    parser.add_argument(
        "--upload-s3",
        action="store_true",
        help="Upload generated report JSON to S3 (optional)",
    )
    parser.add_argument("--bucket", help="S3 bucket name for report upload")
    parser.add_argument("--key", help="S3 object key for report upload")
    parser.add_argument(
        "--endpoint-url",
        default="http://localhost:4566",
        help="S3 endpoint URL (default: http://localhost:4566)",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.upload_s3 and (not args.bucket or not args.key):
        parser.error("--upload-s3 requires both --bucket and --key.")

    try:
        cloud_payload = load_json_file(args.cloud)
        iac_payload = load_json_file(args.iac)

        cloud_resources = extract_resources(cloud_payload, source_name=f"cloud ({args.cloud})")
        iac_resources = extract_resources(iac_payload, source_name=f"iac ({args.iac})")

        match_key = resolve_match_key(
            cloud_resources=cloud_resources,
            iac_resources=iac_resources,
            requested_key=args.match_key,
        )

        report_items = analyze_resources(cloud_resources, iac_resources, match_key)
        if args.format == "array":
            report_payload = [item.to_dict() for item in report_items]
        else:
            report_payload = ResourceReport(
                generatedAt=utc_now_iso8601(),
                matchKeyUsed=match_key,
                totalResources=len(cloud_resources),
                items=report_items,
            ).to_dict()

        report_json = to_json_text(report_payload, pretty=args.pretty)

        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report_json + "\n", encoding="utf-8")
        else:
            print(report_json)

        if args.upload_s3:
            upload_report_to_s3(
                report_json=report_json,
                bucket=args.bucket,
                key=args.key,
                endpoint_url=args.endpoint_url,
            )

    except (LoaderError, MatchKeyError, RuntimeError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0
