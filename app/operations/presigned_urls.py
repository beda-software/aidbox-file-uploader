from datetime import datetime

from aidbox_python_sdk.types import SDKOperation, SDKOperationRequest
from aiobotocore.session import get_session
from aiohttp import web

from app import config
from app.sdk import sdk

upload_schema = {
    "required": [],
    "properties": {
        "resource": {
            "type": "object",
            "required": [],
            "properties": {
                "filename": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
}

download_schema = {
    "required": [],
    "properties": {
        "resource": {
            "type": "object",
            "required": [],
            "properties": {
                "key": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
}


@sdk.operation(["POST"], ["$generate-upload-url"], request_schema=upload_schema)
async def generate_upload_url_op(
    _operation: SDKOperation, request: SDKOperationRequest
) -> web.Response:
    bucket = config.aws_bucket
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = request.get("resource", {}).get("filename", "file.txt")
    name, extension = filename.rsplit(".", 1)
    filename_with_timestamp = f"{name}-{timestamp}.{extension}"
    folder = config.bucket_prefix
    key = f"{folder}/{filename_with_timestamp}"

    session = get_session()

    async with session.create_client(
        "s3",
        region_name=config.region_name,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        endpoint_url=config.minio_endpoint,
    ) as client:

        put_presigned_url = await client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": "application/octet-stream"},
            ExpiresIn=config.link_ttl,
        )

    return web.json_response(
        {
            "filename": filename,
            "put_presigned_url": put_presigned_url,
        }
    )


@sdk.operation(["POST"], ["$generate-download-url"], request_schema=download_schema)
async def generate_download_url_op(
    _operation: SDKOperation, request: SDKOperationRequest
) -> web.Response:
    bucket = config.aws_bucket
    key = request.get("resource", {}).get("key")

    session = get_session()

    async with session.create_client(
        "s3",
        region_name=config.region_name,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
    ) as client:
        get_presigned_url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=config.link_ttl,
        )

    return web.json_response(
        {
            "get_presigned_url": get_presigned_url,
        }
    )
