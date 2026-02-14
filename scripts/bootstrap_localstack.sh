#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="${1:-resource-reports}"
ENDPOINT_URL="${2:-http://localhost:4566}"

# For LocalStack, static dummy credentials are enough.
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"

if aws --endpoint-url "$ENDPOINT_URL" s3api head-bucket --bucket "$BUCKET_NAME" >/dev/null 2>&1; then
  echo "Bucket already exists: $BUCKET_NAME"
  exit 0
fi

aws --endpoint-url "$ENDPOINT_URL" s3api create-bucket --bucket "$BUCKET_NAME" >/dev/null

echo "Created bucket: $BUCKET_NAME"
