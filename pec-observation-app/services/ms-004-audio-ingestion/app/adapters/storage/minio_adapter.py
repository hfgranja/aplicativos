"""MinIO / S3-compatible object storage adapter."""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from ...config import settings


def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def generate_presigned_put(bucket: str, key: str, expires: int = 1800) -> str:
    """Return a presigned PUT URL valid for `expires` seconds."""
    client = _get_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": "audio/mp4"},
        ExpiresIn=expires,
    )


def generate_presigned_get(bucket: str, key: str, expires: int = 3600) -> str:
    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


def delete_object(bucket: str, key: str) -> None:
    client = _get_client()
    client.delete_object(Bucket=bucket, Key=key)


def object_exists(bucket: str, key: str) -> bool:
    client = _get_client()
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False
