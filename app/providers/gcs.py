import asyncio
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from hashlib import sha256
from urllib.parse import quote

from google.auth import default as google_auth_default
from google.auth import iam as google_auth_iam
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.cloud import storage

from app import config

GCS_HOST = "storage.googleapis.com"


@lru_cache(maxsize=1)
def get_client() -> storage.Client:
    # Uses ambient Workload Identity credentials; signs via IAM signBlob impersonation
    # (roles/iam.serviceAccountTokenCreator) instead of a service-account key.
    return storage.Client()


async def generate_signed_url(
    bucket: str, key: str, method: str, content_type: str | None = None
) -> str:
    blob = get_client().bucket(bucket).blob(key)
    sign_kwargs = (
        {"content_type": content_type} if method == "PUT" else {"response_type": content_type}
    )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        lambda: blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=config.link_ttl),
            method=method,
            **sign_kwargs,
        ),
    )


async def generate_download_headers(bucket: str, key: str) -> dict[str, str]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sign_download_headers, bucket, key)


def sign_download_headers(bucket: str, key: str) -> dict[str, str]:
    # Native GCS header-based V4 signing (GOOG4-RSA-SHA256) via IAM signBlob — the same
    # mechanism generate_signed_url uses for query-string signed URLs, but as an
    # Authorization header. Valid ~15 minutes around x-goog-date, matching the original
    # SigV4-header contract this operation was built around.
    credentials, _ = google_auth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    request = GoogleAuthRequest()
    credentials.refresh(request)
    service_account_email = getattr(credentials, "service_account_email", None)
    if not service_account_email:
        raise RuntimeError(
            "gcs_impersonation signing requires Compute Engine (Workload Identity) credentials"
        )
    signer = google_auth_iam.Signer(request, credentials, service_account_email)

    now = datetime.now(UTC)
    date_stamp = now.strftime("%Y%m%d")
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    canonical_uri = f"/{quote(bucket, safe='-_.~/')}/{quote(key, safe='-_.~/')}"
    signed_headers = "host;x-goog-content-sha256;x-goog-date"
    canonical_headers = (
        f"host:{GCS_HOST}\nx-goog-content-sha256:UNSIGNED-PAYLOAD\nx-goog-date:{timestamp}\n"
    )
    canonical_request = "\n".join(
        ["GET", canonical_uri, "", canonical_headers, signed_headers, "UNSIGNED-PAYLOAD"]
    )
    canonical_request_hash = sha256(canonical_request.encode()).hexdigest()

    credential_scope = f"{date_stamp}/auto/storage/goog4_request"
    string_to_sign = "\n".join(
        ["GOOG4-RSA-SHA256", timestamp, credential_scope, canonical_request_hash]
    )
    signature = signer.sign(string_to_sign).hex()
    credential = f"{service_account_email}/{credential_scope}"

    return {
        "Authorization": (
            f"GOOG4-RSA-SHA256 Credential={credential},"
            f"SignedHeaders={signed_headers},Signature={signature}"
        ),
        "x-goog-date": timestamp,
        "x-goog-content-sha256": "UNSIGNED-PAYLOAD",
    }
