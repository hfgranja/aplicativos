import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError
import httpx

logger = logging.getLogger(__name__)

from ...database import get_db
from ...models.feedback import Feedback, FeedbackVersion, ActionItem
from pec_shared.models_base import gen_uuid
from pec_shared.security import decode_token
from ...config import settings
import redis as redis_lib
from pec_shared.events import (
    EventEnvelope, STREAM_FEEDBACK,
    EVT_FEEDBACK_EDITED, EVT_FEEDBACK_HUMAN_REVIEWED, EVT_FEEDBACK_APPROVED,
    publish_event,
)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def _publish(event_type, payload, correlation_id=""):
    try:
        r = redis_lib.from_url(settings.REDIS_URL)
        env = EventEnvelope.create(event_type=event_type, producer="ms-007-feedback",
                                   payload=payload, correlation_id=correlation_id)
        publish_event(r, STREAM_FEEDBACK, env)
    except Exception:
        pass


class FeedbackResponse(BaseModel):
    id: str
    observation_id: str
    strengths: Optional[list]
    improvement_points: Optional[list]
    evidence: Optional[list]
    action_plan: Optional[list]
    summary: Optional[str]
    status: str
    version: int

    class Config:
        from_attributes = True


class FeedbackUpdate(BaseModel):
    strengths: Optional[list] = None
    improvement_points: Optional[list] = None
    evidence: Optional[list] = None
    action_plan: Optional[list] = None
    summary: Optional[str] = None
    edit_reason: Optional[str] = None


class ActionItemCreate(BaseModel):
    description: str
    owner: Optional[str] = "Professor"
    due_date: Optional[str] = None
    expected_evidence: Optional[str] = None


@router.get("/observation/{observation_id}", response_model=FeedbackResponse)
def get_feedback_by_observation(observation_id: str, db: Session = Depends(get_db),
                                 user=Depends(_get_user)):
    fb = db.query(Feedback).filter(Feedback.observation_id == observation_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return fb


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(feedback_id: str, body: FeedbackUpdate,
                    db: Session = Depends(get_db), user=Depends(_get_user)):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    if fb.status == "APPROVED":
        raise HTTPException(status_code=422, detail="Cannot edit approved feedback")

    # Save version before edit
    snapshot = {
        "strengths": fb.strengths, "improvement_points": fb.improvement_points,
        "evidence": fb.evidence, "action_plan": fb.action_plan,
        "summary": fb.summary, "status": fb.status, "version": fb.version,
    }
    version = FeedbackVersion(
        feedback_id=fb.id,
        version_number=fb.version,
        snapshot=snapshot,
        edited_by=user.get("sub", ""),
        edit_reason=body.edit_reason,
    )
    db.add(version)

    for field, value in body.model_dump(exclude_none=True, exclude={"edit_reason"}).items():
        setattr(fb, field, value)
    fb.version += 1
    fb.status = "IN_REVIEW"
    db.commit()
    db.refresh(fb)

    _publish(EVT_FEEDBACK_EDITED,
             {"feedback_id": fb.id, "observation_id": fb.observation_id, "version": fb.version},
             correlation_id=fb.observation_id)
    return fb


@router.post("/{feedback_id}/review", response_model=FeedbackResponse)
def mark_reviewed(feedback_id: str, db: Session = Depends(get_db), user=Depends(_get_user)):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    fb.status = "HUMAN_REVIEWED"
    fb.reviewed_by = user.get("sub", "")
    fb.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(fb)
    _publish(EVT_FEEDBACK_HUMAN_REVIEWED,
             {"feedback_id": fb.id, "observation_id": fb.observation_id},
             correlation_id=fb.observation_id)
    return fb


@router.post("/{feedback_id}/approve", response_model=FeedbackResponse)
def approve_feedback(feedback_id: str, db: Session = Depends(get_db), user=Depends(_get_user)):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    if fb.status != "HUMAN_REVIEWED":
        raise HTTPException(status_code=422, detail="Feedback must be HUMAN_REVIEWED before approval")
    fb.status = "APPROVED"
    fb.approved_by = user.get("sub", "")
    fb.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(fb)
    _publish(EVT_FEEDBACK_APPROVED,
             {"feedback_id": fb.id, "observation_id": fb.observation_id},
             correlation_id=fb.observation_id)

    # Notify MS-013 Learning Engine: store as approved training example
    _notify_learning_engine(fb)

    # Notify MS-014 Evaluator: score AI draft vs. human-approved version
    _notify_evaluator(fb)

    return fb


def _notify_learning_engine(fb) -> None:
    learning_url = settings.LEARNING_SERVICE_URL
    if not learning_url:
        return
    feedback_content = {
        "summary": fb.summary or "",
        "strengths": fb.strengths or [],
        "improvement_points": fb.improvement_points or [],
        "suggested_action_plan": fb.suggested_action_plan or [],
    }
    try:
        httpx.post(
            f"{learning_url}/api/v1/learning/ingest/feedback",
            json={
                "feedback_id": str(fb.id),
                "transcription_snippet": fb.transcription_text or "",
                "feedback_dict": feedback_content,
                "observation_context": {"observation_id": str(fb.observation_id)},
            },
            timeout=5.0,
        )
    except Exception as exc:
        logger.warning("Could not notify learning engine: %s", exc)


def _notify_evaluator(fb) -> None:
    evaluator_url = settings.EVALUATOR_SERVICE_URL
    if not evaluator_url:
        return
    human_feedback = {
        "summary": fb.summary or "",
        "strengths": fb.strengths or [],
        "improvement_points": fb.improvement_points or [],
        "evidence": fb.evidence or [],
        "suggested_action_plan": fb.suggested_action_plan or [],
        "risks_and_uncertainties": fb.risks_and_uncertainties or [],
    }
    # The AI draft is stored in the first FeedbackVersion (version_number=1) snapshot
    ai_draft = {}
    if hasattr(fb, "versions") and fb.versions:
        v1 = min(fb.versions, key=lambda v: v.version_number)
        ai_draft = v1.snapshot or {}
    try:
        httpx.post(
            f"{evaluator_url}/api/v1/evaluator/evaluate",
            json={
                "feedback_id":       str(fb.id),
                "observation_id":    str(fb.observation_id),
                "ai_feedback":       ai_draft or human_feedback,
                "human_feedback":    human_feedback,
                "transcription_text": fb.transcription_text or "",
            },
            timeout=8.0,
        )
    except Exception as exc:
        logger.warning("Could not notify evaluator: %s", exc)


@router.get("/{feedback_id}/versions")
def get_versions(feedback_id: str, db: Session = Depends(get_db), user=Depends(_get_user)):
    versions = db.query(FeedbackVersion).filter(
        FeedbackVersion.feedback_id == feedback_id
    ).order_by(FeedbackVersion.version_number.asc()).all()
    return [
        {"version": v.version_number, "edited_by": v.edited_by,
         "edit_reason": v.edit_reason, "created_at": v.created_at,
         "snapshot": v.snapshot}
        for v in versions
    ]


@router.post("/{feedback_id}/action-items")
def add_action_item(feedback_id: str, body: ActionItemCreate,
                    db: Session = Depends(get_db), user=Depends(_get_user)):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    item = ActionItem(
        feedback_id=feedback_id,
        observation_id=fb.observation_id,
        description=body.description,
        owner=body.owner,
        due_date=body.due_date,
        expected_evidence=body.expected_evidence,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "description": item.description, "owner": item.owner,
            "due_date": item.due_date, "is_completed": item.is_completed}


@router.get("/{feedback_id}/action-items")
def list_action_items(feedback_id: str, db: Session = Depends(get_db), user=Depends(_get_user)):
    items = db.query(ActionItem).filter(ActionItem.feedback_id == feedback_id).all()
    return [
        {"id": i.id, "description": i.description, "owner": i.owner,
         "due_date": i.due_date, "is_completed": i.is_completed,
         "expected_evidence": i.expected_evidence}
        for i in items
    ]
