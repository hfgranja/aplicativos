import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import ActionPlanResult, Observation
from schemas import ActionResultCreate, ActionResultUpdate, ActionResultOut
from services import knowledge_service
from services.llm_service import compute_section_scores
from typing import List

router = APIRouter(prefix="/api/action-results", tags=["action-results"])


@router.post("", response_model=ActionResultOut)
def create_action_result(data: ActionResultCreate, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == data.observation_id).first()
    if not obs:
        raise HTTPException(404, "Observação não encontrada")

    score_before = compute_section_scores(obs).get("total", 0)

    result = ActionPlanResult(
        id=str(uuid.uuid4()),
        observation_id=data.observation_id,
        teacher_id=data.teacher_id,
        action_text=data.action_text,
        action_type=data.action_type,
        deadline=data.deadline,
        responsible=data.responsible,
        status="pendente",
        score_before=score_before,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.get("/teacher/{teacher_id}", response_model=List[ActionResultOut])
def list_teacher_results(teacher_id: str, db: Session = Depends(get_db)):
    return db.query(ActionPlanResult).filter(
        ActionPlanResult.teacher_id == teacher_id
    ).order_by(ActionPlanResult.created_at.desc()).all()


@router.get("/teacher/{teacher_id}/period-comparison")
def period_comparison(teacher_id: str, db: Session = Depends(get_db)):
    return knowledge_service.compute_period_comparison(db, teacher_id)


@router.get("/{result_id}", response_model=ActionResultOut)
def get_action_result(result_id: str, db: Session = Depends(get_db)):
    r = db.query(ActionPlanResult).filter(ActionPlanResult.id == result_id).first()
    if not r:
        raise HTTPException(404, "Resultado não encontrado")
    return r


@router.put("/{result_id}", response_model=ActionResultOut)
def update_action_result(result_id: str, data: ActionResultUpdate, db: Session = Depends(get_db)):
    r = db.query(ActionPlanResult).filter(ActionPlanResult.id == result_id).first()
    if not r:
        raise HTTPException(404, "Resultado não encontrado")

    r.status = data.status
    r.result_notes = data.result_notes
    r.updated_at = datetime.utcnow()

    # If marking as realizado/parcial, try to find next observation score
    if data.status in ("realizado", "parcial"):
        next_obs = db.query(Observation).filter(
            Observation.teacher_id == r.teacher_id,
            Observation.observed_at > db.query(Observation).filter(
                Observation.id == r.observation_id
            ).first().observed_at,
        ).order_by(Observation.observed_at.asc()).first()

        if next_obs:
            score_after = compute_section_scores(next_obs).get("total", 0)
            r.score_after = score_after
            r.delta_score = score_after - (r.score_before or 0)
            r.next_observation_id = next_obs.id

    db.commit()
    db.refresh(r)

    # Index into knowledge base if executed with positive delta
    if data.status == "realizado":
        knowledge_service.index_action_result(db, r)

    return r


@router.delete("/{result_id}")
def delete_action_result(result_id: str, db: Session = Depends(get_db)):
    r = db.query(ActionPlanResult).filter(ActionPlanResult.id == result_id).first()
    if not r:
        raise HTTPException(404, "Resultado não encontrado")
    db.delete(r)
    db.commit()
    return {"ok": True}
