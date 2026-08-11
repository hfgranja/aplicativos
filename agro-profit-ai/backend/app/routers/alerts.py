from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import CurrentUser, get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[schemas.AlertOut])
def list_alerts(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rule + ML Alert Engine output (spec seção 36) across every field in
    the caller's tenant, most recent first."""
    rows = (
        db.query(models.Alert)
        .join(models.Field, models.Alert.field_id == models.Field.id)
        .join(models.Farm, models.Field.farm_id == models.Farm.id)
        .filter(models.Farm.tenant_id == current_user.tenant_id)
        .order_by(models.Alert.triggered_at.desc())
        .all()
    )
    return rows


@router.post("/{alert_id}/acknowledge", response_model=schemas.AlertOut)
def acknowledge_alert(alert_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    field = db.query(models.Field).filter(models.Field.id == alert.field_id).first()
    farm = db.query(models.Farm).filter(models.Farm.id == field.farm_id).first()
    if farm.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Recurso não pertence ao tenant autenticado")
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert
