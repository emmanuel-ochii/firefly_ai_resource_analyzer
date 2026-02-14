"""General helpers for serialization, time, and optional S3 upload."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def utc_now_iso8601() -> str:
    """Return current UTC timestamp in ISO8601 format with trailing Z."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def to_json_text(payload: Any, pretty: bool = False) -> str:
    """Serialize payload to JSON text."""

    if pretty:
        return json.dumps(payload, indent=2, ensure_ascii=False)
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def upload_report_to_s3(
    report_json: str,
    bucket: str,
    key: str,
    endpoint_url: str,
) -> None:
    """Upload a resource report JSON string to S3.

    This is primarily intended for LocalStack in local development,
    but also works with real S3 endpoints if credentials are configured.
    """

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError as exc:
        raise RuntimeError(
            "S3 upload requested, but boto3 is not installed. "
            "Install optional dependency: pip install '.[s3]'"
        ) from exc

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )

    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        error_code = str(exc.response.get("Error", {}).get("Code", ""))
        if error_code in {"404", "NoSuchBucket", "NotFound"}:
            client.create_bucket(Bucket=bucket)
        else:
            raise RuntimeError(
                f"Unable to verify bucket '{bucket}' before upload: {exc}"
            ) from exc

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=report_json.encode("utf-8"),
        ContentType="application/json",
    )
