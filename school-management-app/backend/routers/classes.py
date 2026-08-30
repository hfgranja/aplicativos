from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/classes", tags=["classes"])


def _to_out(c: models.SchoolClass) -> schemas.SchoolClassOut:
    return schemas.SchoolClassOut(
        id=c.id,
        name=c.name,
        grade_level=c.grade_level,
        shift=c.shift,
        school_year=c.school_year,
        student_count=len(c.students),
    )


@router.get("", response_model=List[schemas.SchoolClassOut])
def list_classes(
    school_year: Optional[int] = None,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    q = db.query(models.SchoolClass)
    if school_year:
        q = q.filter(models.SchoolClass.school_year == school_year)
    classes = q.order_by(models.SchoolClass.name).all()
    return [_to_out(c) for c in classes]


@router.post("", response_model=schemas.SchoolClassOut)
def create_class(
    payload: schemas.SchoolClassCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    c = models.SchoolClass(
        name=payload.name,
        grade_level=payload.grade_level,
        shift=payload.shift,
        school_year=payload.school_year or date.today().year,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _to_out(c)


@router.put("/{class_id}", response_model=schemas.SchoolClassOut)
def update_class(
    class_id: str,
    payload: schemas.SchoolClassCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    c = db.query(models.SchoolClass).filter(models.SchoolClass.id == class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    c.name = payload.name
    c.grade_level = payload.grade_level
    c.shift = payload.shift
    if payload.school_year:
        c.school_year = payload.school_year
    db.commit()
    db.refresh(c)
    return _to_out(c)


@router.delete("/{class_id}")
def delete_class(
    class_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    c = db.query(models.SchoolClass).filter(models.SchoolClass.id == class_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    db.delete(c)
    db.commit()
    return {"ok": True}
