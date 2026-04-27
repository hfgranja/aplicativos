"""REST API for MS-012 Best Practices.

Video access is always authenticated — no anonymous presigned URLs.
Clients call GET /api/v1/best-practices/{id}/video-url with a valid
Bearer token and receive a 24-hour presigned URL they play in-app.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from pec_shared.models_base import get_db
from pec_shared.security import decode_token
from ...models.practice import BestPracticeCardModel, DistributionModel
from ...adapters.storage.minio_adapter import (
    video_presigned_url, get_video, get_practice_clip,
)
from ...config import settings

router = APIRouter(prefix="/api/v1/best-practices", tags=["best-practices"])


# ── Auth helper ───────────────────────────────────────────────────────────────

def _get_claims(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_token(token, settings.SECRET_KEY)
    except Exception:
        raise HTTPException(401, "Invalid token")


def _is_authorized_for_video(card_id: str, claims: dict, db: Session) -> bool:
    """Allow PEC roles and teachers with a distribution for this card."""
    role = claims.get("role", "")
    uid  = claims.get("sub", "")
    if role in ("pec", "admin", "coordinator"):
        return True
    # Check teacher distribution
    return db.query(DistributionModel).filter(
        DistributionModel.card_id    == card_id,
        DistributionModel.teacher_id == uid,
    ).first() is not None


# ── Schemas ───────────────────────────────────────────────────────────────────

class PublishRequest(BaseModel):
    title: Optional[str] = None
    tags:  Optional[list[str]] = None

class DistributeRequest(BaseModel):
    teacher_ids: list[str]
    message:     str = ""


# ── Serializer ────────────────────────────────────────────────────────────────

def _serialize(card: BestPracticeCardModel) -> dict:
    return {
        "id":                    card.id,
        "title":                 card.title,
        "criterion":             card.criterion,
        "subject":               card.subject,
        "grade":                 card.grade,
        "excerpt":               card.excerpt,
        "ai_explanation":        card.ai_explanation,
        "rubric_alignment":      json.loads(card.rubric_alignment or "[]"),
        "tags":                  json.loads(card.tags or "[]"),
        "status":                card.status,
        "has_audio":             card.audio_clip_key is not None,
        "video_status":          card.video_status,
        "has_video":             card.video_key is not None and card.video_status == "ready",
        "video_duration_s":      card.video_duration_s,
        "source_observation_id": card.source_observation_id,
        "created_at":            card.created_at,
        "published_at":          card.published_at,
    }


# ── Card CRUD ─────────────────────────────────────────────────────────────────

@router.get("")
def list_cards(
    status:    Optional[str] = Query(None),
    subject:   Optional[str] = Query(None),
    criterion: Optional[str] = Query(None),
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(BestPracticeCardModel)
    if status:    q = q.filter(BestPracticeCardModel.status    == status)
    if subject:   q = q.filter(BestPracticeCardModel.subject.ilike(f"%{subject}%"))
    if criterion: q = q.filter(BestPracticeCardModel.criterion == criterion)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_serialize(c) for c in items], "total": total, "page": page}


@router.get("/{card_id}")
def get_card(card_id: str, db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(
        BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    return _serialize(card)


@router.post("/{card_id}/publish")
def publish_card(card_id: str, req: PublishRequest,
                 db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(
        BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404)
    if req.title:   card.title = req.title
    if req.tags:    card.tags  = json.dumps(req.tags)
    card.status       = "published"
    card.published_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    return _serialize(card)


@router.delete("/{card_id}", status_code=204)
def archive_card(card_id: str, db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(
        BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404)
    card.status = "archived"
    db.commit()


# ── Video endpoint (always authenticated, permanent storage) ──────────────────

@router.get("/{card_id}/video-url")
def get_video_url(
    card_id: str,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Return a fresh 24-hour presigned URL for the practice video.

    Access rules:
      - PEC / admin / coordinator: can access all published or draft cards
      - Teacher: must have a Distribution record for this card
    """
    claims = _get_claims(authorization)

    card = db.query(BestPracticeCardModel).filter(
        BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    if not card.video_key or card.video_status != "ready":
        raise HTTPException(202, detail={
            "video_status": card.video_status,
            "message": "Video is still being generated, try again later",
        })
    if not _is_authorized_for_video(card_id, claims, db):
        raise HTTPException(403, "Not authorized")

    url = video_presigned_url(card.video_key, expires=86400)
    return {
        "url":          url,
        "expires_in_s": 86400,
        "duration_s":   card.video_duration_s,
        "video_status": card.video_status,
    }


@router.get("/{card_id}/video-status")
def get_video_status(card_id: str, db: Session = Depends(get_db)):
    """Poll for video generation progress — no auth required."""
    card = db.query(BestPracticeCardModel).filter(
        BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404)
    return {
        "video_status":  card.video_status,
        "has_video":     card.video_key is not None and card.video_status == "ready",
        "duration_s":    card.video_duration_s,
    }


# ── Distribution ──────────────────────────────────────────────────────────────

@router.post("/{card_id}/distribute", status_code=201)
def distribute(card_id: str, req: DistributeRequest,
               db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(
        BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404)
    if card.status != "published":
        raise HTTPException(400, "Only published cards can be distributed")
    now  = datetime.now(timezone.utc).isoformat()
    rows = []
    for tid in req.teacher_ids:
        d = DistributionModel(
            id=str(uuid.uuid4()), card_id=card_id,
            teacher_id=tid, sent_by_pec="pec",
            message=req.message, sent_at=now,
        )
        db.add(d)
        rows.append({"id": d.id, "teacher_id": tid})
    db.commit()
    return {"distributed": len(rows), "items": rows}


@router.get("/distributions/my")
def my_distributions(teacher_id: str = Query(...), db: Session = Depends(get_db)):
    rows = (
        db.query(DistributionModel, BestPracticeCardModel)
        .join(BestPracticeCardModel,
              DistributionModel.card_id == BestPracticeCardModel.id)
        .filter(DistributionModel.teacher_id == teacher_id)
        .order_by(DistributionModel.sent_at.desc())
        .all()
    )
    return {"items": [
        {"distribution_id": d.id, "card": _serialize(c),
         "message": d.message, "sent_at": d.sent_at, "viewed_at": d.viewed_at}
        for d, c in rows
    ]}


@router.post("/distributions/{dist_id}/viewed")
def mark_viewed(dist_id: str, db: Session = Depends(get_db)):
    dist = db.query(DistributionModel).filter(
        DistributionModel.id == dist_id).first()
    if not dist:
        raise HTTPException(404)
    if not dist.viewed_at:
        dist.viewed_at = datetime.now(timezone.utc).isoformat()
        db.commit()
    return {"viewed_at": dist.viewed_at}
