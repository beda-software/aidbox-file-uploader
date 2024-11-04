from datetime import datetime

from aidbox_python_sdk.types import SDKOperation, SDKOperationRequest
from aiobotocore.session import get_session
from aiohttp import web

from app import config
from app.sdk import sdk


@sdk.operation(["POST"], ["$get-presigned-urls"])
async def generate_presigned_urls_op(
    _operation: SDKOperation, request: SDKOperationRequest
) -> web.Response:
    bucket = "dataintake"
    filename = "file"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename_with_timestamp = f"{filename}-{timestamp}.txt"
    folder = "aiobotocore"
    key = f"{folder}/{filename_with_timestamp}"

    session = get_session()

    async with session.create_client(
        "s3",
        region_name=config.region_name,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_acceess_key,
        endpoint_url=config.minio_endpoint,
    ) as client:
        put_presigned_url = await client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=config.link_ttl,
        )

        get_presigned_url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=config.link_ttl,
        )

    return web.json_response(
        {
            "status": "ok",
            "put_presigned_url": put_presigned_url,
            "get_presigned_url": get_presigned_url,
        }
    )
