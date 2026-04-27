"""MinIO/S3 adapter for best-practice audio clips."""
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from ...config import settings

logger = logging.getLogger(__name__)

BUCKET = "best-practices"


def _client():
    return boto3.client(
        "s3",
        endpoint_url        = settings.MINIO_ENDPOINT,
        aws_access_key_id   = settings.MINIO_ACCESS_KEY,
        aws_secret_access_key = settings.MINIO_SECRET_KEY,
    )


def upload_practice_clip(key: str, data: bytes) -> str:
    import io
    _client().upload_fileobj(io.BytesIO(data), BUCKET, key,
                             ExtraArgs={"ContentType": "audio/mpeg"})
    logger.info("Uploaded practice clip %s", key)
    return key


def get_practice_clip(key: str) -> Optional[bytes]:
    try:
        import io
        buf = io.BytesIO()
        _client().download_fileobj(BUCKET, key, buf)
        return buf.getvalue()
    except ClientError as exc:
        logger.error("Failed to fetch clip %s: %s", key, exc)
        return None


def generate_clip_url(key: str, expires: int = 3600) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params     = {"Bucket": BUCKET, "Key": key},
        ExpiresIn  = expires,
    )
