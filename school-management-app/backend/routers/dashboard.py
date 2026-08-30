from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user
from routers.occurrences import _to_out as occurrence_to_out
from routers.announcements import _to_out as announcement_to_out

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db),
    _user: models.User = Depends(get_current_user),
):
    total_students_active = (
        db.query(models.Student).filter(models.Student.status == "ativo").count()
    )
    total_teachers_active = (
        db.query(models.Teacher).filter(models.Teacher.status == "ativo").count()
    )
    total_classes = db.query(models.SchoolClass).count()

    today = date.today()
    today_records = (
        db.query(models.Attendance).filter(models.Attendance.date == today).all()
    )
    attendance_rate_today = None
    if today_records:
        present_count = sum(1 for r in today_records if r.present)
        attendance_rate_today = round(present_count / len(today_records) * 100, 1)

    recent_occurrences = (
        db.query(models.Occurrence)
        .order_by(models.Occurrence.created_at.desc())
        .limit(5)
        .all()
    )
    recent_announcements = (
        db.query(models.Announcement)
        .order_by(models.Announcement.created_at.desc())
        .limit(5)
        .all()
    )

    return schemas.DashboardStats(
        total_students_active=total_students_active,
        total_teachers_active=total_teachers_active,
        total_classes=total_classes,
        attendance_rate_today=attendance_rate_today,
        recent_occurrences=[occurrence_to_out(o) for o in recent_occurrences],
        recent_announcements=[announcement_to_out(a, db) for a in recent_announcements],
    )
