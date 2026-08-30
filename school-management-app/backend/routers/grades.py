from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/grades", tags=["grades"])


def _to_out(g: models.Grade) -> schemas.GradeOut:
    return schemas.GradeOut(
        id=g.id,
        student_id=g.student_id,
        student_name=g.student.name if g.student else None,
        subject=g.subject,
        term=g.term,
        school_year=g.school_year,
        value=g.value,
        notes=g.notes,
    )


@router.get("", response_model=List[schemas.GradeOut])
def list_grades(
    student_id: Optional[str] = None,
    class_id: Optional[str] = None,
    term: Optional[int] = None,
    school_year: Optional[int] = None,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    q = db.query(models.Grade)
    if student_id:
        q = q.filter(models.Grade.student_id == student_id)
    if class_id:
        q = q.join(models.Student).filter(models.Student.class_id == class_id)
    if term:
        q = q.filter(models.Grade.term == term)
    if school_year:
        q = q.filter(models.Grade.school_year == school_year)
    grades = q.all()
    return [_to_out(g) for g in grades]


@router.post("", response_model=schemas.GradeOut)
def create_grade(
    payload: schemas.GradeCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    data = payload.model_dump()
    if not data.get("school_year"):
        data["school_year"] = date.today().year
    g = models.Grade(**data)
    db.add(g)
    db.commit()
    db.refresh(g)
    return _to_out(g)


@router.put("/{grade_id}", response_model=schemas.GradeOut)
def update_grade(
    grade_id: str,
    payload: schemas.GradeCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    g = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(g, field, value)
    db.commit()
    db.refresh(g)
    return _to_out(g)


@router.delete("/{grade_id}")
def delete_grade(
    grade_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    g = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    db.delete(g)
    db.commit()
    return {"ok": True}
