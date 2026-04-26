from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError

from ...database import get_db
from ...models.teacher import Teacher
from ...models.school import School
from pec_shared.security import decode_token
from ...config import settings
import redis as redis_lib
from pec_shared.events import EventEnvelope, STREAM_SCHOOL, EVT_TEACHER_CREATED, publish_event

router = APIRouter(prefix="/api/v1/teachers", tags=["teachers"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class TeacherCreate(BaseModel):
    school_id: str
    name: str
    registration_number: Optional[str] = None
    subjects: List[str] = []
    grades: List[str] = []


class TeacherResponse(BaseModel):
    id: str
    school_id: str
    name: str
    registration_number: Optional[str]
    subjects: List[str]
    grades: List[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("", response_model=TeacherResponse, status_code=201)
def create_teacher(body: TeacherCreate, db: Session = Depends(get_db),
                   user=Depends(_get_user)):
    school = db.query(School).filter(School.id == body.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    teacher = Teacher(
        school_id=body.school_id, name=body.name,
        registration_number=body.registration_number,
        subjects=body.subjects, grades=body.grades,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    try:
        r = redis_lib.from_url(settings.REDIS_URL)
        env = EventEnvelope.create(
            event_type=EVT_TEACHER_CREATED,
            producer="ms-002-school",
            payload={"teacher_id": teacher.id, "school_id": teacher.school_id, "name": teacher.name},
            correlation_id=teacher.id,
        )
        publish_event(r, STREAM_SCHOOL, env)
    except Exception:
        pass

    return teacher


@router.get("", response_model=List[TeacherResponse])
def list_teachers(school_id: Optional[str] = None, db: Session = Depends(get_db),
                  user=Depends(_get_user)):
    q = db.query(Teacher).filter(Teacher.is_active == True)
    if school_id:
        q = q.filter(Teacher.school_id == school_id)
    return q.all()


@router.get("/{teacher_id}", response_model=TeacherResponse)
def get_teacher(teacher_id: str, db: Session = Depends(get_db), user=Depends(_get_user)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    subjects: Optional[List[str]] = None
    grades: Optional[List[str]] = None


@router.patch("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(teacher_id: str, body: TeacherUpdate,
                   db: Session = Depends(get_db), user=Depends(_get_user)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(teacher, field, value)
    db.commit()
    db.refresh(teacher)
    return teacher
