import asyncio
from datetime import datetime

from aiobotocore.session import get_session

from app import config


async def go() -> None:
    bucket = "dataintake"
    filename = "file"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename_with_timestamp = f"{filename}-{timestamp}.txt"

    # print(filename_with_timestamp)
    folder = "aiobotocore"
    key = f"{folder}/{filename_with_timestamp}"

    # print(config.region_name)
    # print(config.link_ttl)
    # print(config.minio_endpoint)
    # print(config.aws_access_key_id)
    # print(config.aws_secret_acceess_key)

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
            ExpiresIn=config.link_ttl,  # 15 minutes
        )
        print("Presigned URL for upload:", put_presigned_url)  # noqa: T201

        get_presigned_url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=config.link_ttl,  # 15 minutes
        )
        print("Presigned URL for download:", get_presigned_url)  # noqa: T201


if __name__ == "__main__":
    asyncio.run(go())
