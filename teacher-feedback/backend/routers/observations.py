import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import Observation, Teacher, MediaFile, ActionPlanResult
from schemas import ObservationCreate, ObservationOut, CNVRequest
from services import llm_service, knowledge_service
from services.llm_service import compute_section_scores
from typing import List

router = APIRouter(prefix="/api/observations", tags=["observations"])


@router.get("", response_model=List[ObservationOut])
def list_observations(db: Session = Depends(get_db)):
    return db.query(Observation).order_by(Observation.observed_at.desc()).all()


@router.post("", response_model=ObservationOut)
def create_observation(data: ObservationCreate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == data.teacher_id).first()
    if not teacher:
        raise HTTPException(404, "Professor não encontrado")
    obs = Observation(id=str(uuid.uuid4()), **data.model_dump())
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.get("/{obs_id}", response_model=ObservationOut)
def get_observation(obs_id: str, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404, "Observação não encontrada")
    return obs


@router.put("/{obs_id}", response_model=ObservationOut)
def update_observation(obs_id: str, data: ObservationCreate, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404, "Observação não encontrada")
    for k, v in data.model_dump().items():
        setattr(obs, k, v)
    obs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obs)
    return obs


@router.delete("/{obs_id}")
def delete_observation(obs_id: str, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404, "Observação não encontrada")
    db.delete(obs)
    db.commit()
    return {"ok": True}


@router.post("/{obs_id}/generate-feedback")
def generate_feedback(obs_id: str, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404, "Observação não encontrada")
    teacher = db.query(Teacher).filter(Teacher.id == obs.teacher_id).first()

    # Get last 5 observations for RAG context (excluding current)
    history = db.query(Observation).filter(
        Observation.teacher_id == obs.teacher_id,
        Observation.id != obs_id,
        Observation.feedback_raw.isnot(None),
    ).order_by(Observation.observed_at.desc()).limit(5).all()

    # RAG layer 2: executed action plan results
    action_results = db.query(ActionPlanResult).filter(
        ActionPlanResult.teacher_id == obs.teacher_id,
        ActionPlanResult.status.in_(["realizado", "parcial"]),
    ).order_by(ActionPlanResult.updated_at.desc()).limit(10).all()

    # RAG layer 3: best practices from similar context
    grade_band = llm_service.infer_grade_band(teacher.grade or "")
    best_practices = knowledge_service.get_best_practices(
        db, subject=teacher.subject or "", grade_band=grade_band, limit=5
    )

    # Include media transcript if available
    if obs.media_file_id and not obs.transcript:
        media = db.query(MediaFile).filter(MediaFile.id == obs.media_file_id).first()
        if media and media.transcript:
            obs.transcript = media.transcript

    try:
        feedback = llm_service.generate_feedback(obs, teacher, history, action_results, best_practices)
        obs.feedback_raw = json.dumps(feedback, ensure_ascii=False)
        obs.feedback_generated_at = datetime.utcnow()
        db.commit()
        # Auto-index into knowledge base
        knowledge_service.index_observation(db, obs_id)
        return {"ok": True, "feedback": feedback, "scores": compute_section_scores(obs)}
    except Exception as e:
        raise HTTPException(500, f"Erro ao gerar feedback: {str(e)}")


@router.post("/{obs_id}/generate-cnv")
def generate_cnv(obs_id: str, data: CNVRequest, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404, "Observação não encontrada")
    teacher = db.query(Teacher).filter(Teacher.id == obs.teacher_id).first()

    if not data.questions:
        raise HTTPException(400, "Forneça pelo menos uma pergunta")

    try:
        cnv = llm_service.generate_cnv(obs, teacher, data.questions)
        obs.cnv_script = json.dumps(cnv, ensure_ascii=False)
        obs.updated_at = datetime.utcnow()
        db.commit()
        return {"ok": True, "cnv": cnv}
    except Exception as e:
        raise HTTPException(500, f"Erro ao gerar roteiro CNV: {str(e)}")


@router.get("/{obs_id}/scores")
def get_scores(obs_id: str, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == obs_id).first()
    if not obs:
        raise HTTPException(404, "Observação não encontrada")
    return compute_section_scores(obs)
