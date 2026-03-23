from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.release import ReleaseDecision
from app.models.execution import Execution
from app.models.user import User
from app.core.deps import get_current_user
from app.services.release_service import compute_release_decision
from app.schemas.release import ReleaseDecisionOut

router = APIRouter(prefix="/releases", tags=["releases"])


@router.get("/{execution_id}", response_model=ReleaseDecisionOut)
def get_release_decision(execution_id: str, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    ex = db.query(Execution).filter(
        Execution.id == execution_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")

    decision = db.query(ReleaseDecision).filter(ReleaseDecision.execution_id == execution_id).first()
    if not decision:
        if ex.status != "COMPLETED":
            raise HTTPException(status_code=400, detail="Execution not yet completed")
        decision = compute_release_decision(db, execution_id, current_user.id)

    return decision


@router.post("/{execution_id}/generate", response_model=ReleaseDecisionOut)
def generate_release_decision(execution_id: str, db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    ex = db.query(Execution).filter(
        Execution.id == execution_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    if ex.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Execution not yet completed")

    existing = db.query(ReleaseDecision).filter(ReleaseDecision.execution_id == execution_id).first()
    if existing:
        db.delete(existing)
        db.commit()

    return compute_release_decision(db, execution_id, current_user.id)
