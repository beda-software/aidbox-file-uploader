# aidbox-python-sdk-example

## Signing modes

`SIGNING_MODE` controls how presigned upload/download URLs and headers are signed.

| Mode | Default | Use for | Extra env vars needed |
|---|---|---|---|
| `static` | yes | AWS S3, MinIO, GCS with an HMAC key | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `MINIO_ENDPOINT`, `REGION_NAME` |
| `gcs-impersonation` | no | GCS only, no static keys (e.g. GKE Workload Identity) | none — signs via ambient credentials + IAM `signBlob` |

Common to both modes:
- `BUCKET` (or `AWS_BUCKET`, kept for existing deployments — `BUCKET` wins if both are set) — bucket name, required.
- `BUCKET_PREFIX` — key prefix, default `aiobotocore` (historical, kept for backward compat).
- `LINK_TTL` — presigned URL/header validity in seconds, default `600`.

# Development

## Local environment setup

1. Install pyenv and poetry globally
2. Install python3.12 python globally using pyenv
3. Inside the app directory, run `poetry env use /path/to/python312`
4. Run `poetry install`
5. Run `poetry shell` to activate virtual environment
6. Run `autohooks activate` to activate git hooks

## Local deployment
0. Run Aidbox anywhere but make `host.docker.internal` available from the Aidbox to access the host machine
1. Run `cp .env.example .env`
2. `docker-compose up`

## Testing

1. Run `cp .env.tests.local.example .env.tests.local`
2. Put your dev aidbox license key into `AIDBOX_LICENSE_TEST` in `.env.tests.local`
3. Run `docker compose -f compose.test-env.yaml build` at the first time and every time once dependencies are updated/added
4. Run `./run_test.sh`
5. You can kill the containers when complete to work with tests by run:
   `docker compose -f compose.test-env.yaml down`

## IDE setup

Strongly recommended to use ruff and mypy plugins for IDE
