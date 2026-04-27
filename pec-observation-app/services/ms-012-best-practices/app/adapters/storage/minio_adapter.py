"""MinIO/S3 adapter for audio clips and practice videos."""
import io
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
        endpoint_url          = settings.MINIO_ENDPOINT,
        aws_access_key_id     = settings.MINIO_ACCESS_KEY,
        aws_secret_access_key = settings.MINIO_SECRET_KEY,
    )


# ── Audio ─────────────────────────────────────────────────────────────────────

def upload_practice_clip(key: str, data: bytes) -> str:
    _client().upload_fileobj(
        io.BytesIO(data), BUCKET, key,
        ExtraArgs={"ContentType": "audio/mpeg"},
    )
    logger.info("Uploaded clip %s", key)
    return key


def get_practice_clip(key: str) -> Optional[bytes]:
    try:
        buf = io.BytesIO()
        _client().download_fileobj(BUCKET, key, buf)
        return buf.getvalue()
    except ClientError as exc:
        logger.error("Clip download failed %s: %s", key, exc)
        return None


# ── Video ─────────────────────────────────────────────────────────────────────

def upload_video(key: str, data: bytes) -> str:
    _client().upload_fileobj(
        io.BytesIO(data), BUCKET, key,
        ExtraArgs={"ContentType": "video/mp4"},
    )
    logger.info("Uploaded video %s (%.2f MB)", key, len(data) / 1e6)
    return key


def get_video(key: str) -> Optional[bytes]:
    try:
        buf = io.BytesIO()
        _client().download_fileobj(BUCKET, key, buf)
        return buf.getvalue()
    except ClientError as exc:
        logger.error("Video download failed %s: %s", key, exc)
        return None


def video_presigned_url(key: str, expires: int = 86400) -> str:
    """Return a presigned GET URL valid for *expires* seconds (default 24 h)."""
    return _client().generate_presigned_url(
        "get_object",
        Params    = {"Bucket": BUCKET, "Key": key},
        ExpiresIn = expires,
    )
