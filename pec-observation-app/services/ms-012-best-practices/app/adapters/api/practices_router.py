"""REST API for MS-012 Best Practices."""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from pec_shared.models_base import get_db
from ...models.practice import BestPracticeCardModel, DistributionModel
from ...adapters.storage.minio_adapter import generate_clip_url, get_practice_clip

router = APIRouter(prefix="/api/v1/best-practices", tags=["best-practices"])


# ── Schemas ─────────────────────────────────────────────────────────────────

class PublishRequest(BaseModel):
    title:       Optional[str] = None
    tags:        Optional[list[str]] = None

class DistributeRequest(BaseModel):
    teacher_ids: list[str]
    message:     str = ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _serialize(card: BestPracticeCardModel, with_clip_url: bool = False) -> dict:
    d = {
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
        "source_observation_id": card.source_observation_id,
        "created_at":            card.created_at,
        "published_at":          card.published_at,
    }
    if with_clip_url and card.audio_clip_key:
        try:
            d["audio_url"] = generate_clip_url(card.audio_clip_key)
        except Exception:
            d["audio_url"] = None
    return d


# ── Routes ────────────────────────────────────────────────────────────────────

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
    if status:
        q = q.filter(BestPracticeCardModel.status == status)
    if subject:
        q = q.filter(BestPracticeCardModel.subject.ilike(f"%{subject}%"))
    if criterion:
        q = q.filter(BestPracticeCardModel.criterion == criterion)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_serialize(c) for c in items], "total": total, "page": page}


@router.get("/{card_id}")
def get_card(card_id: str, db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    return _serialize(card, with_clip_url=True)


@router.post("/{card_id}/publish")
def publish_card(card_id: str, req: PublishRequest, db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    if req.title:
        card.title = req.title
    if req.tags is not None:
        card.tags = json.dumps(req.tags)
    card.status       = "published"
    card.published_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    return _serialize(card)


@router.delete("/{card_id}", status_code=204)
def archive_card(card_id: str, db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    card.status = "archived"
    db.commit()


@router.get("/{card_id}/audio")
def stream_audio(card_id: str, db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(BestPracticeCardModel.id == card_id).first()
    if not card or not card.audio_clip_key:
        raise HTTPException(404, "Audio not available")
    data = get_practice_clip(card.audio_clip_key)
    if data is None:
        raise HTTPException(404, "Audio clip missing from storage")
    return Response(content=data, media_type="audio/mpeg")


@router.post("/{card_id}/distribute", status_code=201)
def distribute(card_id: str, req: DistributeRequest, db: Session = Depends(get_db)):
    card = db.query(BestPracticeCardModel).filter(BestPracticeCardModel.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    if card.status != "published":
        raise HTTPException(400, "Only published cards can be distributed")

    now     = datetime.now(timezone.utc).isoformat()
    created = []
    for tid in req.teacher_ids:
        dist = DistributionModel(
            id          = str(uuid.uuid4()),
            card_id     = card_id,
            teacher_id  = tid,
            sent_by_pec = "pec",  # TODO: inject from JWT
            message     = req.message,
            sent_at     = now,
        )
        db.add(dist)
        created.append({"id": dist.id, "teacher_id": tid})
    db.commit()
    return {"distributed": len(created), "items": created}


@router.get("/distributions/my")
def my_distributions(
    teacher_id: str = Query(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DistributionModel, BestPracticeCardModel)
        .join(BestPracticeCardModel, DistributionModel.card_id == BestPracticeCardModel.id)
        .filter(DistributionModel.teacher_id == teacher_id)
        .order_by(DistributionModel.sent_at.desc())
        .all()
    )
    items = []
    for dist, card in rows:
        items.append({
            "distribution_id": dist.id,
            "card":            _serialize(card, with_clip_url=True),
            "message":         dist.message,
            "sent_at":         dist.sent_at,
            "viewed_at":       dist.viewed_at,
        })
    return {"items": items}


@router.post("/distributions/{dist_id}/viewed", status_code=200)
def mark_viewed(dist_id: str, db: Session = Depends(get_db)):
    dist = db.query(DistributionModel).filter(DistributionModel.id == dist_id).first()
    if not dist:
        raise HTTPException(404)
    if not dist.viewed_at:
        dist.viewed_at = datetime.now(timezone.utc).isoformat()
        db.commit()
    return {"viewed_at": dist.viewed_at}
