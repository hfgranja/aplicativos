from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/students", tags=["students"])


def _to_out(s: models.Student) -> schemas.StudentOut:
    return schemas.StudentOut(
        id=s.id,
        name=s.name,
        ra=s.ra,
        birth_date=s.birth_date,
        class_id=s.class_id,
        class_name=s.school_class.name if s.school_class else None,
        status=s.status,
        guardian_name=s.guardian_name,
        guardian_phone=s.guardian_phone,
        guardian_email=s.guardian_email,
        address=s.address,
        enrollment_date=s.enrollment_date,
        notes=s.notes,
    )


@router.get("", response_model=List[schemas.StudentOut])
def list_students(
    class_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    q = db.query(models.Student)
    if class_id:
        q = q.filter(models.Student.class_id == class_id)
    if status:
        q = q.filter(models.Student.status == status)
    if search:
        q = q.filter(models.Student.name.ilike(f"%{search}%"))
    students = q.order_by(models.Student.name).all()
    return [_to_out(s) for s in students]


@router.get("/{student_id}", response_model=schemas.StudentOut)
def get_student(
    student_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    s = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return _to_out(s)


@router.post("", response_model=schemas.StudentOut)
def create_student(
    payload: schemas.StudentCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    s = models.Student(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return _to_out(s)


@router.put("/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: str,
    payload: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    s = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return _to_out(s)


@router.delete("/{student_id}")
def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    s = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    db.delete(s)
    db.commit()
    return {"ok": True}
