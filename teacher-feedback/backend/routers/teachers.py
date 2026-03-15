from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Teacher
from schemas import TeacherCreate, TeacherOut
from typing import List
import uuid

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


@router.get("", response_model=List[TeacherOut])
def list_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).order_by(Teacher.name).all()


@router.post("", response_model=TeacherOut)
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db)):
    teacher = Teacher(id=str(uuid.uuid4()), **data.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.get("/{teacher_id}", response_model=TeacherOut)
def get_teacher(teacher_id: str, db: Session = Depends(get_db)):
    t = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not t:
        raise HTTPException(404, "Professor não encontrado")
    return t


@router.put("/{teacher_id}", response_model=TeacherOut)
def update_teacher(teacher_id: str, data: TeacherCreate, db: Session = Depends(get_db)):
    t = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not t:
        raise HTTPException(404, "Professor não encontrado")
    for k, v in data.model_dump().items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: str, db: Session = Depends(get_db)):
    t = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not t:
        raise HTTPException(404, "Professor não encontrado")
    db.delete(t)
    db.commit()
    return {"ok": True}


@router.get("/{teacher_id}/observations")
def get_teacher_observations(teacher_id: str, db: Session = Depends(get_db)):
    from models import Observation
    from services.llm_service import compute_section_scores
    t = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not t:
        raise HTTPException(404, "Professor não encontrado")
    obs_list = db.query(Observation).filter(
        Observation.teacher_id == teacher_id
    ).order_by(Observation.observed_at.desc()).all()

    result = []
    for obs in obs_list:
        scores = compute_section_scores(obs)
        result.append({
            "id": obs.id,
            "observed_at": obs.observed_at.isoformat() if obs.observed_at else None,
            "pec_name": obs.pec_name,
            "focus_area": obs.focus_area,
            "has_feedback": bool(obs.feedback_raw),
            "has_cnv": bool(obs.cnv_script),
            "has_media": bool(obs.media_file_id),
            "scores": scores,
            "created_at": obs.created_at.isoformat() if obs.created_at else None,
        })
    return result
