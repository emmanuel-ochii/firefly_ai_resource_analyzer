# Resource Analyzer

`resource_analyzer` compares cloud resources with IaC resources and emits a JSON resource report.

## Runtime and packaging

- Python: 3.11+
- Packaging approach: plain `pip`/`setuptools` (no uv-specific project config)

## Project layout

- `src/resource_analyzer/`: package source
- `tests/`: pytest test suite
- `Dockerfile.localstack`: LocalStack Dockerfile for the bonus requirement
- `docker/localstack/init/10-create-bucket.sh`: auto-creates S3 bucket on LocalStack readiness
- `docker-compose.yml`: optional LocalStack S3 environment
- `scripts/bootstrap_localstack.sh`: optional manual helper to create/ensure a bucket

```text
.
├── Dockerfile.localstack
├── README.md
├── docker-compose.yml
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

Run as a module:

```bash
python -m resource_analyzer --cloud cloud.json --iac iac.json --match-key name --out report.json --pretty
```

Arguments:

- `--cloud PATH` (required)
- `--iac PATH` (required)
- `--match-key KEY` (optional if auto-detection succeeds)
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

The report is a JSON object:

```json
{
  "GeneratedAt": "2026-02-12T00:00:00Z",
  "MatchKeyUsed": "name",
  "TotalResources": 1,
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

- `TotalResources` is the number of cloud resources analyzed.
- `State` is one of: `Missing`, `Match`, `Modified`.
- `ChangeLog` is populated only for `Modified`.
- `KeyName` paths use dotted keys and list indices (example: `spec.containers[0].image`).
- List ordering matters because arrays are diffed by index.

## Tests

```bash
pytest
```

Coverage includes:

- Loader structure normalization and errors.
- Diff behavior for missing/match/modified resources.
- Nested dictionary differences.
- List index differences.
- Missing key differences (`null` vs value).
- CLI smoke execution with temporary files.

## Optional: LocalStack S3 upload

Build and start LocalStack (uses `Dockerfile.localstack`):

```bash
docker compose up -d
```

The compose service sets `REPORTS_BUCKET_NAME=resource-reports`, and the init script at
`docker/localstack/init/10-create-bucket.sh` creates it automatically when LocalStack is ready.

If you want to create/verify a bucket manually:

```bash
bash scripts/bootstrap_localstack.sh resource-reports
```

Run analyzer with upload:

```bash
python -m resource_analyzer \
  --cloud cloud.json \
  --iac iac.json \
  --match-key name \
  --upload-s3 \
  --bucket resource-reports \
  --key reports/latest.json \
  --endpoint-url http://localhost:4566
```

The program ensures the bucket exists before uploading.
