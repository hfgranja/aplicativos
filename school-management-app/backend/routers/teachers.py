from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


@router.get("", response_model=List[schemas.TeacherOut])
def list_teachers(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    q = db.query(models.Teacher)
    if status:
        q = q.filter(models.Teacher.status == status)
    return q.order_by(models.Teacher.name).all()


@router.post("", response_model=schemas.TeacherOut)
def create_teacher(
    payload: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    t = models.Teacher(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.put("/{teacher_id}", response_model=schemas.TeacherOut)
def update_teacher(
    teacher_id: str,
    payload: schemas.TeacherUpdate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    t = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    t = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    db.delete(t)
    db.commit()
    return {"ok": True}


# ---------- Assignments (atribuição de aulas) ----------
@router.get("/assignments/all", response_model=List[schemas.AssignmentOut])
def list_assignments(
    class_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    q = db.query(models.TeacherAssignment)
    if class_id:
        q = q.filter(models.TeacherAssignment.class_id == class_id)
    if teacher_id:
        q = q.filter(models.TeacherAssignment.teacher_id == teacher_id)
    results = []
    for a in q.all():
        results.append(
            schemas.AssignmentOut(
                id=a.id,
                teacher_id=a.teacher_id,
                teacher_name=a.teacher.name if a.teacher else None,
                class_id=a.class_id,
                class_name=a.school_class.name if a.school_class else None,
                subject=a.subject,
            )
        )
    return results


@router.post("/assignments", response_model=schemas.AssignmentOut)
def create_assignment(
    payload: schemas.AssignmentCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    teacher = db.query(models.Teacher).filter(models.Teacher.id == payload.teacher_id).first()
    school_class = db.query(models.SchoolClass).filter(models.SchoolClass.id == payload.class_id).first()
    if not teacher or not school_class:
        raise HTTPException(status_code=404, detail="Professor ou turma não encontrado")
    a = models.TeacherAssignment(**payload.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return schemas.AssignmentOut(
        id=a.id,
        teacher_id=a.teacher_id,
        teacher_name=teacher.name,
        class_id=a.class_id,
        class_name=school_class.name,
        subject=a.subject,
    )


@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    a = (
        db.query(models.TeacherAssignment)
        .filter(models.TeacherAssignment.id == assignment_id)
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail="Atribuição não encontrada")
    db.delete(a)
    db.commit()
    return {"ok": True}
