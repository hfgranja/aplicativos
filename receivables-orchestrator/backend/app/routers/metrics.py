from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_merchant_from_api_key, require_merchant_match
from app.services import metrics as metrics_service
from app.services import reconciliation as reconciliation_service

router = APIRouter(prefix="/receivables", tags=["metrics"])


@router.get("/metrics", response_model=schemas.MetricsOut)
def get_metrics(merchant_id: str, period: int = 30, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                 db: Session = Depends(get_db)):
    require_merchant_match(merchant_id, merchant)
    return metrics_service.compute_metrics(db, merchant_id, period)


@router.get("/settlements", response_model=list[schemas.SettlementOut])
def get_settlements(merchant_id: str, period: int = 30, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                     db: Session = Depends(get_db)):
    require_merchant_match(merchant_id, merchant)
    return metrics_service.list_settlements(db, merchant_id, period)


@router.post("/settlements/{settlement_id}/resolve-exception", response_model=schemas.SettlementOut)
def resolve_exception(settlement_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                       db: Session = Depends(get_db)):
    settlement = db.get(models.Settlement, settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Liquidação não encontrada")
    reconciliation_service.resolve_exception(db, settlement_id)
    db.refresh(settlement)
    return schemas.SettlementOut(
        id=settlement.id, attempt_id=settlement.attempt_id, gross_amount=settlement.gross_amount,
        fee=settlement.fee, net_amount=settlement.net_amount,
        expected_settlement_at=settlement.expected_settlement_at, settled_at=settlement.settled_at,
        reconciled=bool(settlement.reconciliation and settlement.reconciliation.matched),
        discrepancy_amount=settlement.reconciliation.discrepancy_amount if settlement.reconciliation else 0.0,
    )
