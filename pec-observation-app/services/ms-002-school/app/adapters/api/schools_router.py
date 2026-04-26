from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError

from ...database import get_db
from ...models.school import School
from ...models.teacher import Teacher
from pec_shared.models_base import gen_uuid
from pec_shared.security import decode_token
from ...config import settings
import redis as redis_lib
from pec_shared.events import EventEnvelope, STREAM_SCHOOL, EVT_SCHOOL_CREATED, publish_event

router = APIRouter(prefix="/api/v1/schools", tags=["schools"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class SchoolCreate(BaseModel):
    name: str
    city: str
    district: str
    external_reference: Optional[str] = None


class SchoolResponse(BaseModel):
    id: str
    name: str
    city: str
    district: str
    external_reference: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("", response_model=SchoolResponse, status_code=201)
def create_school(body: SchoolCreate, db: Session = Depends(get_db),
                  user=Depends(_get_user)):
    existing = db.query(School).filter(
        School.name == body.name, School.city == body.city
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="School already exists in this city")

    school = School(
        name=body.name, city=body.city,
        district=body.district, external_reference=body.external_reference,
    )
    db.add(school)
    db.commit()
    db.refresh(school)

    try:
        r = redis_lib.from_url(settings.REDIS_URL)
        env = EventEnvelope.create(
            event_type=EVT_SCHOOL_CREATED,
            producer="ms-002-school",
            payload={"school_id": school.id, "name": school.name, "city": school.city},
            correlation_id=school.id,
            causation_id=user.get("sub", ""),
        )
        publish_event(r, STREAM_SCHOOL, env)
    except Exception:
        pass  # Event publishing is best-effort; don't fail the request

    return school


@router.get("", response_model=List[SchoolResponse])
def list_schools(db: Session = Depends(get_db), user=Depends(_get_user)):
    return db.query(School).filter(School.is_active == True).all()


@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(school_id: str, db: Session = Depends(get_db), user=Depends(_get_user)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    external_reference: Optional[str] = None


@router.patch("/{school_id}", response_model=SchoolResponse)
def update_school(school_id: str, body: SchoolUpdate,
                  db: Session = Depends(get_db), user=Depends(_get_user)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(school, field, value)
    db.commit()
    db.refresh(school)
    return school
