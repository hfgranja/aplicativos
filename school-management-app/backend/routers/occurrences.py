from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/occurrences", tags=["occurrences"])


def _to_out(o: models.Occurrence) -> schemas.OccurrenceOut:
    return schemas.OccurrenceOut(
        id=o.id,
        student_id=o.student_id,
        student_name=o.student.name if o.student else None,
        date=o.date,
        type=o.type,
        description=o.description,
        action_taken=o.action_taken,
        guardian_notified=o.guardian_notified,
        reported_by=o.reported_by,
        reported_by_name=None,
        created_at=o.created_at,
    )


@router.get("", response_model=List[schemas.OccurrenceOut])
def list_occurrences(
    student_id: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    q = db.query(models.Occurrence)
    if student_id:
        q = q.filter(models.Occurrence.student_id == student_id)
    if type:
        q = q.filter(models.Occurrence.type == type)
    records = q.order_by(models.Occurrence.date.desc()).all()
    out = []
    for o in records:
        item = _to_out(o)
        reporter = db.query(models.User).filter(models.User.id == o.reported_by).first()
        item.reported_by_name = reporter.name if reporter else None
        out.append(item)
    return out


@router.post("", response_model=schemas.OccurrenceOut)
def create_occurrence(
    payload: schemas.OccurrenceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    data = payload.model_dump()
    if not data.get("date"):
        data.pop("date", None)
    o = models.Occurrence(**data, reported_by=current_user.id)
    db.add(o)
    db.commit()
    db.refresh(o)
    item = _to_out(o)
    item.reported_by_name = current_user.name
    return item


@router.put("/{occurrence_id}", response_model=schemas.OccurrenceOut)
def update_occurrence(
    occurrence_id: str,
    payload: schemas.OccurrenceCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    o = db.query(models.Occurrence).filter(models.Occurrence.id == occurrence_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(o, field, value)
    db.commit()
    db.refresh(o)
    return _to_out(o)


@router.delete("/{occurrence_id}")
def delete_occurrence(
    occurrence_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    o = db.query(models.Occurrence).filter(models.Occurrence.id == occurrence_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    db.delete(o)
    db.commit()
    return {"ok": True}
