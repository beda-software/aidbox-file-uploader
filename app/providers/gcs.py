import asyncio
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from hashlib import sha256
from urllib.parse import quote

from google.auth import default as google_auth_default
from google.auth import iam as google_auth_iam
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.cloud import storage

from app import config
from app.providers import DownloadHeaders

GCS_HOST = "storage.googleapis.com"


@lru_cache(maxsize=1)
def get_client() -> storage.Client:
    # Uses ambient Workload Identity credentials; signs via IAM signBlob impersonation
    # (roles/iam.serviceAccountTokenCreator) instead of a service-account key.
    return storage.Client()


@lru_cache(maxsize=1)
def get_ambient_credentials() -> Credentials:
    credentials, _ = google_auth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return credentials


def get_signing_identity() -> tuple[Credentials, str]:
    # storage.Client()'s own credentials aren't Signing-capable under real Workload
    # Identity (only google.auth.credentials.Signing subclasses are, and ambient
    # Compute Engine credentials aren't one) — blob.generate_signed_url() needs an
    # explicit service_account_email + access_token to sign via IAM signBlob instead.
    credentials = get_ambient_credentials()
    if not credentials.valid:
        credentials.refresh(GoogleAuthRequest())
    service_account_email = getattr(credentials, "service_account_email", None)
    if not service_account_email:
        raise RuntimeError(
            "gcs-impersonation signing requires Compute Engine (Workload Identity) credentials"
        )

    return credentials, service_account_email


async def generate_signed_url(
    bucket: str, key: str, method: str, content_type: str | None = None
) -> str:
    sign_kwargs = (
        {"content_type": content_type}
        if method == "PUT"
        else ({"response_type": content_type} if content_type else {})
    )

    def sign() -> str:
        credentials, service_account_email = get_signing_identity()
        blob = get_client().bucket(bucket).blob(key)
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=config.link_ttl),
            method=method,
            service_account_email=service_account_email,
            access_token=credentials.token,
            **sign_kwargs,
        )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sign)


async def generate_download_headers(bucket: str, key: str) -> DownloadHeaders:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sign_download_headers, bucket, key)


def sign_download_headers(bucket: str, key: str) -> DownloadHeaders:
    # Native GCS header-based V4 signing (GOOG4-RSA-SHA256) via IAM signBlob — the same
    # mechanism generate_signed_url uses for query-string signed URLs, but as an
    # Authorization header. Valid ~15 minutes around x-goog-date, matching the original
    # SigV4-header contract this operation was built around.
    credentials, service_account_email = get_signing_identity()
    signer = google_auth_iam.Signer(GoogleAuthRequest(), credentials, service_account_email)

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
        "url": f"https://{GCS_HOST}{canonical_uri}",
        "headers": {
            "Authorization": (
                f"GOOG4-RSA-SHA256 Credential={credential},"
                f"SignedHeaders={signed_headers},Signature={signature}"
            ),
            "x-goog-date": timestamp,
            "x-goog-content-sha256": "UNSIGNED-PAYLOAD",
        },
    }
