from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError

from ...database import get_db
from ...models.transcription import Transcription
from pec_shared.security import decode_token
from ...config import settings

router = APIRouter(prefix="/api/v1/transcriptions", tags=["transcriptions"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.get("/{observation_id}")
def get_transcription(observation_id: str, db: Session = Depends(get_db),
                      user=Depends(_get_user)):
    t = db.query(Transcription).filter(Transcription.observation_id == observation_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return {
        "transcription_id": t.id,
        "observation_id": t.observation_id,
        "status": t.status,
        "full_text": t.full_text,
        "segments": t.segments,
        "language": t.language,
        "duration_seconds": t.duration_seconds,
        "segment_count": t.segment_count,
        "model_used": t.model_used,
        "completed_at": t.completed_at,
    }
