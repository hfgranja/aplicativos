from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError

from ...database import get_db
from ...models.consent import ConsentRecord, DeletionSchedule
from pec_shared.security import decode_token
from ...config import settings
import redis as redis_lib
from pec_shared.events import EventEnvelope, STREAM_CONSENT, EVT_CONSENT_RECORDED, publish_event

router = APIRouter(prefix="/api/v1/consents", tags=["consents"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class ConsentCreate(BaseModel):
    observation_id: str
    consent_type: str  # audio_recording | data_processing
    version: str = "v1.0"


class ConsentResponse(BaseModel):
    id: str
    observation_id: str
    consent_type: str
    accepted_by_user_id: str
    accepted_at: datetime
    version: str

    class Config:
        from_attributes = True


@router.post("", response_model=ConsentResponse, status_code=201)
def record_consent(body: ConsentCreate, request: Request,
                   db: Session = Depends(get_db), user=Depends(_get_user)):
    consent = ConsentRecord(
        observation_id=body.observation_id,
        consent_type=body.consent_type,
        accepted_by_user_id=user.get("sub", ""),
        version=body.version,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    try:
        r = redis_lib.from_url(settings.REDIS_URL)
        env = EventEnvelope.create(
            event_type=EVT_CONSENT_RECORDED,
            producer="ms-010-consent",
            payload={"consent_id": consent.id, "observation_id": body.observation_id,
                     "consent_type": body.consent_type},
            correlation_id=body.observation_id,
        )
        publish_event(r, STREAM_CONSENT, env)
    except Exception:
        pass

    return consent


@router.get("/{observation_id}", response_model=List[ConsentResponse])
def get_consents(observation_id: str, db: Session = Depends(get_db), user=Depends(_get_user)):
    return db.query(ConsentRecord).filter(
        ConsentRecord.observation_id == observation_id
    ).all()
