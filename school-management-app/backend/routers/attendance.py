from datetime import date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def _to_out(a: models.Attendance) -> schemas.AttendanceOut:
    return schemas.AttendanceOut(
        id=a.id,
        student_id=a.student_id,
        student_name=a.student.name if a.student else None,
        class_id=a.class_id,
        date=a.date,
        present=a.present,
        justified=a.justified,
        notes=a.notes,
    )


@router.get("", response_model=List[schemas.AttendanceOut])
def list_attendance(
    class_id: Optional[str] = None,
    student_id: Optional[str] = None,
    date: Optional[date_type] = None,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    q = db.query(models.Attendance)
    if class_id:
        q = q.filter(models.Attendance.class_id == class_id)
    if student_id:
        q = q.filter(models.Attendance.student_id == student_id)
    if date:
        q = q.filter(models.Attendance.date == date)
    records = q.order_by(models.Attendance.date.desc()).all()
    return [_to_out(a) for a in records]


@router.post("/bulk", response_model=List[schemas.AttendanceOut])
def record_bulk_attendance(
    payload: schemas.AttendanceBulkCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    """Lança/atualiza a frequência de uma turma inteira para uma data."""
    school_class = (
        db.query(models.SchoolClass).filter(models.SchoolClass.id == payload.class_id).first()
    )
    if not school_class:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    results = []
    for entry in payload.entries:
        existing = (
            db.query(models.Attendance)
            .filter(
                models.Attendance.class_id == payload.class_id,
                models.Attendance.student_id == entry.student_id,
                models.Attendance.date == payload.date,
            )
            .first()
        )
        if existing:
            existing.present = entry.present
            existing.justified = entry.justified
            existing.notes = entry.notes
            record = existing
        else:
            record = models.Attendance(
                student_id=entry.student_id,
                class_id=payload.class_id,
                date=payload.date,
                present=entry.present,
                justified=entry.justified,
                notes=entry.notes,
            )
            db.add(record)
        results.append(record)
    db.commit()
    for r in results:
        db.refresh(r)
    return [_to_out(r) for r in results]


@router.delete("/{attendance_id}")
def delete_attendance(
    attendance_id: str,
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    a = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    db.delete(a)
    db.commit()
    return {"ok": True}
