from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_merchant_from_api_key, require_merchant_match

router = APIRouter(tags=["merchants"])


@router.get("/merchants", response_model=list[schemas.MerchantOut])
def list_merchants(db: Session = Depends(get_db)):
    """Endpoint de conveniencia para a demo (trocar de estabelecimento no
    seletor do frontend). Em producao isto nunca exporia api_key em uma
    listagem publica — aqui e deliberado para fins didaticos."""
    return db.query(models.Merchant).all()


@router.get("/merchants/{merchant_id}/customers", response_model=list[schemas.CustomerOut])
def list_customers(merchant_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                    db: Session = Depends(get_db)):
    require_merchant_match(merchant_id, merchant)
    return db.query(models.Customer).filter(models.Customer.merchant_id == merchant_id).all()


@router.get("/merchants/{merchant_id}/policy", response_model=schemas.MerchantPolicyOut)
def get_policy(merchant_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
               db: Session = Depends(get_db)):
    require_merchant_match(merchant_id, merchant)
    policy = (
        db.query(models.MerchantPolicy)
        .filter(models.MerchantPolicy.merchant_id == merchant_id, models.MerchantPolicy.is_default.is_(True))
        .first()
    )
    if not policy:
        raise HTTPException(status_code=404, detail="Política não encontrada")
    return policy


@router.put("/merchants/{merchant_id}/policy", response_model=schemas.MerchantPolicyOut)
def update_policy(merchant_id: str, payload: schemas.MerchantPolicyIn,
                   merchant: models.Merchant = Depends(get_merchant_from_api_key), db: Session = Depends(get_db)):
    require_merchant_match(merchant_id, merchant)
    policy = (
        db.query(models.MerchantPolicy)
        .filter(models.MerchantPolicy.merchant_id == merchant_id, models.MerchantPolicy.is_default.is_(True))
        .first()
    )
    if not policy:
        policy = models.MerchantPolicy(merchant_id=merchant_id, is_default=True)
        db.add(policy)

    policy.name = payload.name
    policy.objective = payload.objective
    policy.weights = payload.weights.model_dump()
    policy.max_exposure = payload.max_exposure
    policy.allowed_methods = payload.allowed_methods
    policy.operation_mode = payload.operation_mode
    policy.confidence_threshold = payload.confidence_threshold
    db.commit()
    db.refresh(policy)

    from app.services import audit
    audit.record(db, actor=f"user:merchant_admin", action="policy_updated", entity_type="MerchantPolicy",
                 entity_id=policy.id, after=payload.model_dump())
    return policy
