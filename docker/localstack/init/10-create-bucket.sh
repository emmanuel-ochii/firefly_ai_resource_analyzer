#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="${REPORTS_BUCKET_NAME:-resource-reports}"

if awslocal s3api head-bucket --bucket "$BUCKET_NAME" >/dev/null 2>&1; then
  echo "Bucket already exists: $BUCKET_NAME"
  exit 0
fi

awslocal s3api create-bucket --bucket "$BUCKET_NAME" >/dev/null
echo "Created bucket: $BUCKET_NAME"
