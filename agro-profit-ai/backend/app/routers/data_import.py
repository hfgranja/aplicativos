from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import CurrentUser, get_current_user, require_farm_in_tenant

router = APIRouter(prefix="/data", tags=["data-import"])


def _owned_field(field_id: str, current_user: CurrentUser, db: Session) -> models.Field:
    field = db.query(models.Field).filter(models.Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Talhão não encontrado")
    farm = db.query(models.Farm).filter(models.Farm.id == field.farm_id).first()
    require_farm_in_tenant(farm, current_user)
    return field


@router.post("/soil/import", response_model=schemas.SoilSampleOut)
def import_soil_sample(payload: schemas.SoilSampleIn, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Soil Laboratory Importer (spec seção 6) — producer/lab-uploaded
    samples always take precedence over SoilGrids for their field."""
    _owned_field(payload.field_id, current_user, db)
    sample = models.SoilSample(**payload.model_dump(), source="laboratory")
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


@router.post("/yield/import", response_model=schemas.YieldRecordOut)
def import_yield_record(payload: schemas.YieldRecordIn, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_field(payload.field_id, current_user, db)
    record = models.YieldRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/operations/import", response_model=schemas.OperationOut)
def import_operation(payload: schemas.OperationIn, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_field(payload.field_id, current_user, db)
    operation = models.Operation(**payload.model_dump())
    db.add(operation)
    db.commit()
    db.refresh(operation)
    return operation
