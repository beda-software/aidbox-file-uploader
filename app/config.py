import os

is_test_environment = os.environ.get("TEST_ENV", False)

aws_bucket = os.environ.get("AWS_BUCKET", "dataintake")
bucket_prefix = os.environ.get("BUCKET_PREFIX", "aiobotocore")
link_ttl = int(os.environ.get("LINK_TTL", "600"))
region_name = os.environ["REGION_NAME"]
aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
minio_endpoint = os.environ["MINIO_ENDPOINT"]
