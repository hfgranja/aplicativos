from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.policy import Policy
from app.models.user import User
from app.core.deps import get_current_user
from app.core.audit_logger import log_event
from app.schemas.policy import PolicyCreate, PolicyOut

router = APIRouter(prefix="/policies", tags=["policies"])


@router.post("", response_model=PolicyOut)
def create_policy(body: PolicyCreate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    policy = Policy(tenant_id=current_user.tenant_id, created_by=current_user.id, **body.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    log_event(db, "policy.created", user_id=current_user.id, tenant_id=current_user.tenant_id,
              resource_type="policy", resource_id=policy.id)
    return policy


@router.get("", response_model=List[PolicyOut])
def list_policies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Policy).filter(
        Policy.tenant_id == current_user.tenant_id, Policy.is_active == True
    ).all()


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    policy = db.query(Policy).filter(
        Policy.id == policy_id, Policy.tenant_id == current_user.tenant_id
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/{policy_id}", response_model=PolicyOut)
def update_policy(policy_id: str, body: PolicyCreate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    policy = db.query(Policy).filter(
        Policy.id == policy_id, Policy.tenant_id == current_user.tenant_id
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(policy, k, v)
    policy.version += 1
    db.commit()
    db.refresh(policy)
    log_event(db, "policy.updated", user_id=current_user.id, tenant_id=current_user.tenant_id,
              resource_type="policy", resource_id=policy_id,
              payload={"version": policy.version})
    return policy
