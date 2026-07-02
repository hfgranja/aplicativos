from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_merchant_from_api_key
from app.services import audit as audit_service

router = APIRouter(prefix="/receivables", tags=["audit"])


@router.get("/audit-log", response_model=list[schemas.AuditLogOut])
def list_audit_log(entity_id: str | None = None, limit: int = 100,
                    merchant: models.Merchant = Depends(get_merchant_from_api_key), db: Session = Depends(get_db)):
    query = db.query(models.AuditLog)
    if entity_id:
        query = query.filter(models.AuditLog.entity_id == entity_id)
    return query.order_by(models.AuditLog.timestamp.desc()).limit(limit).all()


@router.get("/audit-log/verify")
def verify_audit_chain(merchant: models.Merchant = Depends(get_merchant_from_api_key), db: Session = Depends(get_db)):
    ok = audit_service.verify_chain(db)
    return {"chain_valid": ok}


@router.get("/alerts", response_model=list[schemas.AlertOut])
def list_alerts(merchant: models.Merchant = Depends(get_merchant_from_api_key), db: Session = Depends(get_db),
                 limit: int = 50):
    return (
        db.query(models.Alert)
        .filter(models.Alert.merchant_id == merchant.id)
        .order_by(models.Alert.created_at.desc())
        .limit(limit)
        .all()
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=schemas.AlertOut)
def acknowledge_alert(alert_id: str, merchant: models.Merchant = Depends(get_merchant_from_api_key),
                       db: Session = Depends(get_db)):
    alert = db.get(models.Alert, alert_id)
    if alert:
        alert.acknowledged = True
        db.commit()
        db.refresh(alert)
    return alert
