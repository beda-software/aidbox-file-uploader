import asyncio
import logging

from aiobotocore.session import get_session

# .env
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""


async def go() -> None:
    bucket = "dataintake"
    filename = "dummy.bin"
    folder = "aiobotocore"
    key = f"{folder}/{filename}"

    session = get_session()
    async with session.create_client(
        "s3",
        region_name="us-west-2",
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        # .env
        endpoint_url="",
    ) as client:
        put_presigned_url = await client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=900,  # 15 minutes
        )
        logging.info("Presigned URL for upload:", put_presigned_url)  # noqa: PLE1205

        get_presigned_url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=900,  # 15 minutes
        )
        logging.info("Presigned URL for download:", get_presigned_url)  # noqa: PLE1205


if __name__ == "__main__":
    asyncio.run(go())
