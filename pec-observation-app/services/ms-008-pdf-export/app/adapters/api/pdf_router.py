from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError

import boto3
from botocore.config import Config

from ...database import get_db
from ...models.pdf_export import PDFExport
from pec_shared.security import decode_token
from ...config import settings

router = APIRouter(prefix="/api/v1/pdf", tags=["pdf"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.get("/{observation_id}/download-url")
def get_download_url(observation_id: str, db: Session = Depends(get_db),
                     user=Depends(_get_user)):
    export = db.query(PDFExport).filter(
        PDFExport.observation_id == observation_id,
        PDFExport.status == "COMPLETED",
    ).order_by(PDFExport.generated_at.desc()).first()
    if not export:
        raise HTTPException(status_code=404, detail="PDF not available")

    client = boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.MINIO_BUCKET_PDF, "Key": export.minio_key},
        ExpiresIn=settings.PDF_PRESIGNED_EXPIRY_SECONDS,
    )
    return {"download_url": url, "integrity_hash": export.integrity_hash,
            "generated_at": export.generated_at}
