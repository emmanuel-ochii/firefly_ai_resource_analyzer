# Resource Analyzer

`resource_analyzer` compares cloud resources with IaC resources and emits a JSON report.

## Requirements (Read First)

- **Python 3.9+ supported** (3.11 recommended)
- Docker Desktop (optional, only for LocalStack/S3 bonus)
- AWS CLI (optional, only for manual S3 verification)

Quick check:

```bash
python3 --version
```

## Runtime and packaging

- Packaging approach: plain `pip`/`setuptools` (no uv-specific project config)

## Project layout

- `src/resource_analyzer/`: package source
- `tests/`: pytest test suite
- `examples/`: sample cloud/iac input files
- `Dockerfile.localstack`: LocalStack Dockerfile for bonus requirement
- `docker/localstack/init/10-create-bucket.sh`: auto-creates S3 bucket on LocalStack readiness
- `docker-compose.yml`: optional LocalStack S3 environment
- `scripts/bootstrap_localstack.sh`: optional manual helper to create/ensure a bucket

```text
.
├── Dockerfile.localstack
├── README.md
├── docker-compose.yml
├── examples/
│   ├── cloud.json
│   └── iac.json
├── pyproject.toml
├── docker/
│   └── localstack/
│       └── init/
│           └── 10-create-bucket.sh
├── scripts/
│   └── bootstrap_localstack.sh
├── src/
│   └── resource_analyzer/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── diff.py
│       ├── loader.py
│       ├── models.py
│       └── utils.py
└── tests/
    ├── test_cli_smoke.py
    ├── test_diff.py
    └── test_loader.py
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Install dev/test dependencies:

```bash
pip install -e '.[dev]'
```

Install optional S3 upload dependencies:

```bash
pip install -e '.[s3]'
```

## Usage

Run with sample files:

```bash
python -m resource_analyzer \
  --cloud examples/cloud.json \
  --iac examples/iac.json \
  --match-key name \
  --out report.json \
  --pretty
```

Run with bare array output (`--format array`):

```bash
python -m resource_analyzer \
  --cloud examples/cloud.json \
  --iac examples/iac.json \
  --match-key name \
  --format array \
  --out report-array.json \
  --pretty
```

Arguments:

- `--cloud PATH` (required)
- `--iac PATH` (required)
- `--match-key KEY` (optional if auto-detection succeeds)
- `--format {wrapped,array}` (optional, default `wrapped`)
- `--out PATH` (optional)
- `--pretty` (optional)
- `--upload-s3` (optional)
- `--bucket BUCKET` (required when `--upload-s3` is set)
- `--key KEY` (required when `--upload-s3` is set)
- `--endpoint-url URL` (optional, default `http://localhost:4566`)

If `--match-key` is omitted, auto-detection checks in order:

1. `id`
2. `resourceId`
3. `arn`
4. `name`

If none exists in both datasets, the CLI exits with an explicit error and asks for `--match-key`.

## Input format

Each input JSON can be either:

1. A top-level list of resource objects.
2. A top-level object containing a list under one of: `resources`, `items`, `data`.

Anything else causes a clear loader error.

## Output format

### `--format wrapped` (default)

```json
{
  "GeneratedAt": "2026-02-12T00:00:00Z",
  "MatchKeyUsed": "name",
  "TotalResources": 3,
  "Resources": [
    {
      "CloudResourceItem": {},
      "IacResourceItem": {},
      "State": "Match",
      "ChangeLog": []
    }
  ]
}
```

### `--format array`

```json
[
  {
    "CloudResourceItem": {},
    "IacResourceItem": {},
    "State": "Match",
    "ChangeLog": []
  }
]
```

Notes:

- `TotalResources` is the number of cloud resources analyzed.
- `State` is one of: `Missing`, `Match`, `Modified`.
- `ChangeLog` is populated only for `Modified`.
- `KeyName` paths use dotted keys and list indices (example: `spec.containers[0].image`).
- List ordering matters because arrays are diffed by index.

## Tests

```bash
pytest
```

Coverage report:

```bash
pytest --cov=src/resource_analyzer --cov-report=term-missing
```

## Optional: LocalStack S3 upload

Build and start LocalStack (uses `Dockerfile.localstack`):

```bash
docker compose up -d --build
```

The compose service sets `REPORTS_BUCKET_NAME=resource-reports`, and the init script at
`docker/localstack/init/10-create-bucket.sh` creates it automatically when LocalStack is ready.

If you want to create/verify a bucket manually (requires AWS CLI):

```bash
bash scripts/bootstrap_localstack.sh resource-reports
```

Run analyzer with upload:

```bash
python -m resource_analyzer \
  --cloud examples/cloud.json \
  --iac examples/iac.json \
  --match-key name \
  --upload-s3 \
  --bucket resource-reports \
  --key reports/latest.json \
  --endpoint-url http://localhost:4566 \
  --out report.json \
  --pretty
```

The program ensures the bucket exists before uploading.

## Compatibility note (`slots=True` fallback)

This project supports Python 3.9+. In `models.py`, dataclass creation uses a version-aware helper that applies `slots=True` on Python 3.10+ and falls back to plain dataclasses on Python 3.9.
