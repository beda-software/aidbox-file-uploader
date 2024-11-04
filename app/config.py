import os

is_test_environment = os.environ.get("TEST_ENV", False)

link_ttl = int(os.environ.get("LINK_TTL", "600"))
region_name = os.environ["REGION_NAME"]
minio_endpoint = os.environ["MINIO_ENDPOINT"]
aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
aws_secret_acceess_key = os.environ["AWS_SECRET_ACCESS_KEY"]
