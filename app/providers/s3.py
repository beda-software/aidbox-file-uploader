from aiobotocore.session import get_session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

from app import config


async def generate_signed_url(
    bucket: str, key: str, method: str, content_type: str | None = None
) -> str:
    session = get_session()

    async with session.create_client(
        "s3",
        region_name=config.region_name,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        endpoint_url=config.minio_endpoint,
    ) as client:
        if method == "PUT":
            params = {"Bucket": bucket, "Key": key}
            if content_type:
                params["ContentType"] = content_type
            return await client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=config.link_ttl,
            )

        params = {"Bucket": bucket, "Key": key}
        if content_type:
            params["ResponseContentType"] = content_type
        return await client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=config.link_ttl,
        )


def generate_download_headers(bucket: str, key: str) -> dict[str, str]:
    url = f"{config.minio_endpoint}/{bucket}/{key}"
    credentials = Credentials(
        access_key=config.aws_access_key_id,
        secret_key=config.aws_secret_access_key,
    )
    headers = {
        "x-amz-content-sha256": "UNSIGNED-PAYLOAD",
    }

    aws_request = AWSRequest(
        method="GET",
        url=url,
        headers=headers,
    )

    signer = SigV4Auth(credentials, "s3", config.region_name)
    signer.add_auth(aws_request)

    return dict(aws_request.headers)
