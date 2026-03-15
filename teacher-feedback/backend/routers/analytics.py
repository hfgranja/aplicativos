from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Observation, Teacher
from services.analytics_service import compute_evolution, compute_comparative

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/teacher/{teacher_id}/evolution")
def evolution(teacher_id: str, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(404, "Professor não encontrado")
    observations = db.query(Observation).filter(
        Observation.teacher_id == teacher_id
    ).order_by(Observation.observed_at).all()
    return compute_evolution(observations)


@router.get("/teacher/{teacher_id}/comparative")
def comparative(teacher_id: str, obs1: str, obs2: str, db: Session = Depends(get_db)):
    o1 = db.query(Observation).filter(Observation.id == obs1, Observation.teacher_id == teacher_id).first()
    o2 = db.query(Observation).filter(Observation.id == obs2, Observation.teacher_id == teacher_id).first()
    if not o1 or not o2:
        raise HTTPException(404, "Uma ou ambas as observações não encontradas")
    return compute_comparative(o1, o2)
