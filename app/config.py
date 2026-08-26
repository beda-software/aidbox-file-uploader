import os

is_test_environment = os.environ.get("TEST_ENV", False)

aws_bucket = os.environ.get("BUCKET") or os.environ.get("AWS_BUCKET") or "dataintake"
bucket_prefix = os.environ.get("BUCKET_PREFIX", "aiobotocore")
link_ttl = int(os.environ.get("LINK_TTL", "600"))

region_name = os.environ.get("REGION_NAME")
aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
minio_endpoint = os.environ.get("MINIO_ENDPOINT")

# "static" signs with AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY (AWS S3, MinIO, GCS with an HMAC key).
# "gcs-impersonation" signs via GCS's IAM signBlob API using ambient credentials
# (e.g. GKE Workload Identity) instead of a static key.
STATIC = "static"
GCS_IMPERSONATION = "gcs-impersonation"
SIGNING_MODES = (STATIC, GCS_IMPERSONATION)

signing_mode = os.environ.get("SIGNING_MODE", STATIC)
if signing_mode not in SIGNING_MODES:
    raise ValueError(f"SIGNING_MODE must be one of {SIGNING_MODES}, got {signing_mode!r}")
