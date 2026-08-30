from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


def _to_out(a: models.Announcement, db: Session) -> schemas.AnnouncementOut:
    creator = db.query(models.User).filter(models.User.id == a.created_by).first()
    school_class = (
        db.query(models.SchoolClass).filter(models.SchoolClass.id == a.class_id).first()
        if a.class_id
        else None
    )
    return schemas.AnnouncementOut(
        id=a.id,
        title=a.title,
        body=a.body,
        class_id=a.class_id,
        class_name=school_class.name if school_class else None,
        created_by=a.created_by,
        created_by_name=creator.name if creator else None,
        created_at=a.created_at,
    )


@router.get("", response_model=List[schemas.AnnouncementOut])
def list_announcements(
    class_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    q = db.query(models.Announcement)
    if class_id:
        q = q.filter(models.Announcement.class_id == class_id)
    records = q.order_by(models.Announcement.created_at.desc()).all()
    return [_to_out(a, db) for a in records]


@router.post("", response_model=schemas.AnnouncementOut)
def create_announcement(
    payload: schemas.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    a = models.Announcement(**payload.model_dump(), created_by=current_user.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return _to_out(a, db)


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    a = db.query(models.Announcement).filter(models.Announcement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Comunicado não encontrado")
    db.delete(a)
    db.commit()
    return {"ok": True}
