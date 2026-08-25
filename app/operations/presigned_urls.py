from datetime import datetime

from aidbox_python_sdk.types import SDKOperation, SDKOperationRequest
from aiohttp import web

from app import config
from app.providers import gcs as gcs_provider
from app.providers import s3 as s3_provider
from app.sdk import sdk

upload_schema = {
    "required": [],
    "properties": {
        "resource": {
            "type": "object",
            "required": [],
            "properties": {
                "filename": {"type": "string"},
                "content_type": {"type": "string"},
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
                "content_type": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
}


@sdk.operation(["POST"], ["fhir", "$generate-upload-url"], request_schema=upload_schema)
@sdk.operation(["POST"], ["$generate-upload-url"], request_schema=upload_schema)
async def generate_upload_url_op(
    _operation: SDKOperation, request: SDKOperationRequest
) -> web.Response:
    bucket = config.aws_bucket
    resource = request.get("resource", {})
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = resource.get("filename", "file.txt")
    content_type = resource.get("content_type") or "application/octet-stream"
    name, extension = filename.rsplit(".", 1)
    filename_with_timestamp = f"{name}-{timestamp}.{extension}"
    folder = config.bucket_prefix
    key = f"{folder}/{filename_with_timestamp}"

    put_presigned_url = await generate_signed_url(bucket, key, "PUT", content_type=content_type)

    return web.json_response(
        {
            "filename": key,
            "put_presigned_url": put_presigned_url,
        }
    )


@sdk.operation(["POST"], ["fhir", "$generate-download-url"], request_schema=download_schema)
@sdk.operation(["POST"], ["$generate-download-url"], request_schema=download_schema)
async def generate_download_url_op(
    _operation: SDKOperation, request: SDKOperationRequest
) -> web.Response:
    bucket = config.aws_bucket
    resource = request.get("resource", {})
    key = resource.get("key")
    content_type = resource.get("content_type")

    if not key:
        raise web.HTTPBadRequest(reason="resource.key is required")

    get_presigned_url = await generate_signed_url(bucket, key, "GET", content_type=content_type)

    return web.json_response(
        {
            "get_presigned_url": get_presigned_url,
        }
    )


async def generate_signed_url(
    bucket: str, key: str, method: str, content_type: str | None = None
) -> str:
    if config.signing_mode == "gcs_impersonation":
        return await gcs_provider.generate_signed_url(
            bucket, key, method, content_type=content_type
        )
    return await s3_provider.generate_signed_url(bucket, key, method, content_type=content_type)


@sdk.operation(["POST"], ["fhir", "$generate-download-headers"], request_schema=download_schema)
@sdk.operation(["POST"], ["$generate-download-headers"], request_schema=download_schema)
async def generate_download_headers_op(
    _operation: SDKOperation, request: SDKOperationRequest
) -> web.Response:
    bucket = config.aws_bucket
    key = request.get("resource", {}).get("key")

    if not key:
        raise web.HTTPBadRequest(reason="resource.key is required")

    headers = await generate_download_headers(bucket, key)

    return web.json_response(headers)


async def generate_download_headers(bucket: str, key: str) -> dict[str, str]:
    if config.signing_mode == "gcs_impersonation":
        return await gcs_provider.generate_download_headers(bucket, key)
    return s3_provider.generate_download_headers(bucket, key)
