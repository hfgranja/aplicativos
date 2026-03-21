from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.application import Application
from app.models.user import User
from app.core.deps import get_current_user
from app.core.audit_logger import log_event
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationOut

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationOut)
def create_application(body: ApplicationCreate, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    app = Application(tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(app)
    db.commit()
    db.refresh(app)
    log_event(db, "application.created", user_id=current_user.id, tenant_id=current_user.tenant_id,
              resource_type="application", resource_id=app.id, payload={"name": app.name})
    return app


@router.get("", response_model=List[ApplicationOut])
def list_applications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Application).filter(
        Application.tenant_id == current_user.tenant_id,
        Application.is_active == True,
    ).all()


@router.get("/{app_id}", response_model=ApplicationOut)
def get_application(app_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    app = db.query(Application).filter(
        Application.id == app_id, Application.tenant_id == current_user.tenant_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{app_id}", response_model=ApplicationOut)
def update_application(app_id: str, body: ApplicationUpdate, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    app = db.query(Application).filter(
        Application.id == app_id, Application.tenant_id == current_user.tenant_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(app, k, v)
    db.commit()
    db.refresh(app)
    log_event(db, "application.updated", user_id=current_user.id, tenant_id=current_user.tenant_id,
              resource_type="application", resource_id=app.id)
    return app


@router.delete("/{app_id}")
def delete_application(app_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    app = db.query(Application).filter(
        Application.id == app_id, Application.tenant_id == current_user.tenant_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.is_active = False
    db.commit()
    log_event(db, "application.deleted", user_id=current_user.id, tenant_id=current_user.tenant_id,
              resource_type="application", resource_id=app_id)
    return {"detail": "Application deactivated"}
