from unittest.mock import patch

import pytest
from aidbox_python_sdk.aidboxpy import AsyncAidboxClient
from fhirpy.base.exceptions import OperationOutcome

from app import config

GENERATE_SIGNED_URL = "app.operations.presigned_urls.generate_signed_url"
GENERATE_DOWNLOAD_HEADERS = "app.operations.presigned_urls.generate_download_headers"


async def test_generate_upload_url(aidbox_client: AsyncAidboxClient) -> None:
    with patch(GENERATE_SIGNED_URL, return_value="https://example.com/signed-put") as mock:
        output = await aidbox_client.execute(
            "$generate-upload-url",
            method="POST",
            data={"filename": "photo.jpg", "content_type": "image/jpeg"},
        )
    assert output["put_presigned_url"] == "https://example.com/signed-put"
    assert output["filename"].startswith(f"{config.bucket_prefix}/photo-")
    assert output["filename"].endswith(".jpg")

    mock.assert_awaited_once_with(
        config.aws_bucket, output["filename"], "PUT", content_type="image/jpeg"
    )


async def test_generate_upload_url_defaults(aidbox_client: AsyncAidboxClient) -> None:
    with patch(GENERATE_SIGNED_URL, return_value="https://example.com/signed-put"):
        output = await aidbox_client.execute("$generate-upload-url", method="POST", data={})

    assert output["filename"].startswith(f"{config.bucket_prefix}/file-")
    assert output["filename"].endswith(".txt")


async def test_generate_upload_url_dotless_filename(aidbox_client: AsyncAidboxClient) -> None:
    with patch(GENERATE_SIGNED_URL, return_value="https://example.com/signed-put"):
        output = await aidbox_client.execute(
            "$generate-upload-url", method="POST", data={"filename": "README"}
        )

    name = output["filename"].rsplit("/", 1)[1]
    assert name.startswith("README-")
    assert "." not in name


async def test_generate_download_url(aidbox_client: AsyncAidboxClient) -> None:
    with patch(GENERATE_SIGNED_URL, return_value="https://example.com/signed-get") as mock:
        output = await aidbox_client.execute(
            "$generate-download-url",
            method="POST",
            data={"key": "photo.jpg"},
        )

    assert output["get_presigned_url"] == "https://example.com/signed-get"
    mock.assert_awaited_once_with(config.aws_bucket, "photo.jpg", "GET", content_type=None)


async def test_generate_download_url_requires_key(aidbox_client: AsyncAidboxClient) -> None:
    with pytest.raises(OperationOutcome):
        await aidbox_client.execute("$generate-download-url", method="POST", data={})


async def test_generate_download_headers(aidbox_client: AsyncAidboxClient) -> None:
    with patch(GENERATE_DOWNLOAD_HEADERS, return_value={"Authorization": "test-signature"}) as mock:
        output = await aidbox_client.execute(
            "$generate-download-headers",
            method="POST",
            data={"key": "photo.jpg"},
        )

    assert output == {"Authorization": "test-signature"}
    mock.assert_awaited_once_with(config.aws_bucket, "photo.jpg")


async def test_generate_download_headers_requires_key(aidbox_client: AsyncAidboxClient) -> None:
    with pytest.raises(OperationOutcome):
        await aidbox_client.execute("$generate-download-headers", method="POST", data={})
