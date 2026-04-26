from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError

from ...database import get_db
from ...models.audio_upload import AudioUpload
from ...adapters.storage import minio_adapter
from pec_shared.models_base import gen_uuid
from pec_shared.security import decode_token
from ...config import settings
import redis as redis_lib
from pec_shared.events import (
    EventEnvelope, STREAM_AUDIO,
    EVT_AUDIO_UPLOAD_REQUESTED, EVT_AUDIO_UPLOADED, publish_event,
)

router = APIRouter(prefix="/api/v1/audio", tags=["audio"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class PresignedURLRequest(BaseModel):
    observation_id: str
    file_name: str
    file_size_bytes: int
    checksum: str
    codec: str = "aac"
    idempotency_key: Optional[str] = None


class PresignedURLResponse(BaseModel):
    upload_id: str
    upload_url: str
    expires_at: datetime
    method: str = "PUT"


class ConfirmUploadRequest(BaseModel):
    duration_seconds: Optional[int] = None


@router.post("/presigned-url", response_model=PresignedURLResponse, status_code=201)
def get_presigned_url(body: PresignedURLRequest, db: Session = Depends(get_db),
                      user=Depends(_get_user)):
    # Idempotency check
    if body.idempotency_key:
        existing = db.query(AudioUpload).filter(
            AudioUpload.idempotency_key == body.idempotency_key
        ).first()
        if existing and existing.status != "FAILED":
            # Re-generate URL for idempotent re-request
            key = existing.minio_key
            url = minio_adapter.generate_presigned_put(
                settings.MINIO_BUCKET_AUDIO, key, settings.PRESIGNED_URL_EXPIRY_SECONDS
            )
            expires = datetime.utcnow() + timedelta(seconds=settings.PRESIGNED_URL_EXPIRY_SECONDS)
            return PresignedURLResponse(upload_id=existing.id, upload_url=url, expires_at=expires)

    upload_id = gen_uuid()
    minio_key = f"audio/{body.observation_id}/{upload_id}.m4a"
    expires_at = datetime.utcnow() + timedelta(seconds=settings.PRESIGNED_URL_EXPIRY_SECONDS)

    upload = AudioUpload(
        id=upload_id,
        observation_id=body.observation_id,
        minio_key=minio_key,
        status="PENDING",
        file_size_bytes=body.file_size_bytes,
        checksum=body.checksum,
        codec=body.codec,
        idempotency_key=body.idempotency_key,
        upload_url_expires_at=expires_at,
        created_by=user.get("sub", ""),
    )
    db.add(upload)
    db.commit()

    upload_url = minio_adapter.generate_presigned_put(
        settings.MINIO_BUCKET_AUDIO, minio_key, settings.PRESIGNED_URL_EXPIRY_SECONDS
    )

    try:
        r = redis_lib.from_url(settings.REDIS_URL)
        env = EventEnvelope.create(
            event_type=EVT_AUDIO_UPLOAD_REQUESTED,
            producer="ms-004-audio-ingestion",
            payload={"upload_id": upload_id, "observation_id": body.observation_id},
            correlation_id=body.observation_id,
            causation_id=upload_id,
        )
        publish_event(r, STREAM_AUDIO, env)
    except Exception:
        pass

    return PresignedURLResponse(upload_id=upload_id, upload_url=upload_url, expires_at=expires_at)


@router.post("/confirm/{upload_id}")
def confirm_upload(upload_id: str, body: ConfirmUploadRequest = ConfirmUploadRequest(),
                   db: Session = Depends(get_db), user=Depends(_get_user)):
    upload = db.query(AudioUpload).filter(AudioUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.status == "CONFIRMED":
        return {"upload_id": upload_id, "status": "CONFIRMED"}

    # Verify object exists in MinIO
    if not minio_adapter.object_exists(settings.MINIO_BUCKET_AUDIO, upload.minio_key):
        raise HTTPException(status_code=422, detail="Audio file not found in storage")

    upload.status = "CONFIRMED"
    upload.confirmed_at = datetime.utcnow()
    if body.duration_seconds:
        upload.duration_seconds = body.duration_seconds
    db.commit()

    try:
        r = redis_lib.from_url(settings.REDIS_URL)
        env = EventEnvelope.create(
            event_type=EVT_AUDIO_UPLOADED,
            producer="ms-004-audio-ingestion",
            payload={
                "upload_id": upload_id,
                "observation_id": upload.observation_id,
                "minio_key": upload.minio_key,
                "checksum": upload.checksum,
                "codec": upload.codec,
                "duration_seconds": upload.duration_seconds,
                "file_size_bytes": upload.file_size_bytes,
            },
            correlation_id=upload.observation_id,
            causation_id=upload_id,
        )
        publish_event(r, STREAM_AUDIO, env)
    except Exception:
        pass

    return {"upload_id": upload_id, "status": "CONFIRMED", "observation_id": upload.observation_id}


@router.get("/{upload_id}/status")
def get_upload_status(upload_id: str, db: Session = Depends(get_db),
                      user=Depends(_get_user)):
    upload = db.query(AudioUpload).filter(AudioUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return {"upload_id": upload_id, "status": upload.status,
            "observation_id": upload.observation_id}
