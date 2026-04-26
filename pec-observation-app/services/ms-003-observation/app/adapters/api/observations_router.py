from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError

from ...database import get_db
from ...models.observation import Observation
from ...models.status_history import StatusHistory
from ...domain.observation import ObservationStatus, ObservationDomain, DomainError, VALID_TRANSITIONS
from pec_shared.security import decode_token
from ...config import settings
import redis as redis_lib
from pec_shared.events import (
    EventEnvelope, STREAM_OBSERVATION,
    EVT_OBSERVATION_CREATED, EVT_OBSERVATION_STATUS_CHANGED, publish_event,
)

router = APIRouter(prefix="/api/v1/observations", tags=["observations"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def _publish(settings, event_type, payload, correlation_id="", causation_id=""):
    try:
        r = redis_lib.from_url(settings.REDIS_URL)
        env = EventEnvelope.create(
            event_type=event_type,
            producer="ms-003-observation",
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        publish_event(r, STREAM_OBSERVATION, env)
    except Exception:
        pass


class ObservationCreate(BaseModel):
    school_id: str
    teacher_id: str
    subject: str
    grade: str
    lesson_theme: str
    lesson_objectives: Optional[str] = None


class ObservationResponse(BaseModel):
    id: str
    school_id: str
    teacher_id: str
    subject: str
    grade: str
    lesson_theme: str
    lesson_objectives: Optional[str]
    status: str
    audio_duration_seconds: Optional[int]
    audio_checksum: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StatusTransition(BaseModel):
    new_status: str
    notes: Optional[str] = None
    audio_minio_key: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    audio_checksum: Optional[str] = None
    audio_codec: Optional[str] = None


@router.post("", response_model=ObservationResponse, status_code=201)
def create_observation(body: ObservationCreate, db: Session = Depends(get_db),
                       user=Depends(_get_user)):
    obs = Observation(
        school_id=body.school_id,
        teacher_id=body.teacher_id,
        subject=body.subject,
        grade=body.grade,
        lesson_theme=body.lesson_theme,
        lesson_objectives=body.lesson_objectives,
        status=ObservationStatus.DRAFT.value,
        created_by=user.get("sub", "unknown"),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)

    _publish(settings, EVT_OBSERVATION_CREATED,
             {"observation_id": obs.id, "teacher_id": obs.teacher_id, "school_id": obs.school_id},
             correlation_id=obs.id)

    return obs


@router.get("", response_model=List[ObservationResponse])
def list_observations(status_filter: Optional[str] = None,
                      school_id: Optional[str] = None,
                      teacher_id: Optional[str] = None,
                      db: Session = Depends(get_db), user=Depends(_get_user)):
    q = db.query(Observation)
    if status_filter:
        q = q.filter(Observation.status == status_filter)
    if school_id:
        q = q.filter(Observation.school_id == school_id)
    if teacher_id:
        q = q.filter(Observation.teacher_id == teacher_id)
    return q.order_by(Observation.created_at.desc()).all()


@router.get("/{observation_id}", response_model=ObservationResponse)
def get_observation(observation_id: str, db: Session = Depends(get_db),
                    user=Depends(_get_user)):
    obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")
    return obs


@router.patch("/{observation_id}/status", response_model=ObservationResponse)
def transition_status(observation_id: str, body: StatusTransition,
                      db: Session = Depends(get_db), user=Depends(_get_user)):
    obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")

    try:
        new_status = ObservationStatus(body.new_status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown status: {body.new_status}")

    domain = ObservationDomain(
        id=obs.id, school_id=obs.school_id, teacher_id=obs.teacher_id,
        subject=obs.subject, grade=obs.grade, lesson_theme=obs.lesson_theme,
        lesson_objectives=obs.lesson_objectives or "",
        status=ObservationStatus(obs.status),
        created_by=obs.created_by,
    )
    try:
        domain.transition_to(new_status, by=user.get("sub", ""))
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    old_status = obs.status
    obs.status = new_status.value
    if body.audio_minio_key:
        obs.audio_minio_key = body.audio_minio_key
    if body.audio_duration_seconds:
        obs.audio_duration_seconds = body.audio_duration_seconds
    if body.audio_checksum:
        obs.audio_checksum = body.audio_checksum
    if body.audio_codec:
        obs.audio_codec = body.audio_codec

    history = StatusHistory(
        observation_id=obs.id,
        from_status=old_status,
        to_status=new_status.value,
        transitioned_by=user.get("sub", ""),
        notes=body.notes,
    )
    db.add(history)
    db.commit()
    db.refresh(obs)

    _publish(settings, EVT_OBSERVATION_STATUS_CHANGED,
             {"observation_id": obs.id, "from_status": old_status, "to_status": new_status.value},
             correlation_id=obs.id)

    return obs


@router.get("/{observation_id}/status-history")
def get_status_history(observation_id: str, db: Session = Depends(get_db),
                       user=Depends(_get_user)):
    history = db.query(StatusHistory).filter(
        StatusHistory.observation_id == observation_id
    ).order_by(StatusHistory.transitioned_at.asc()).all()
    return [
        {"id": h.id, "from": h.from_status, "to": h.to_status,
         "by": h.transitioned_by, "at": h.transitioned_at, "notes": h.notes}
        for h in history
    ]
