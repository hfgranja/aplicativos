from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.core.deps import get_current_admin
from app.core.audit_logger import log_event
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantOut

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantOut)
def create_tenant(body: TenantCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    if db.query(Tenant).filter(Tenant.slug == body.slug).first():
        raise HTTPException(status_code=400, detail="Slug already in use")
    tenant = Tenant(**body.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    log_event(db, "tenant.created", user_id=current_user.id, resource_type="tenant", resource_id=tenant.id)
    return tenant


@router.get("", response_model=List[TenantOut])
def list_tenants(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    return db.query(Tenant).all()


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(tenant_id: str, body: TenantUpdate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_admin)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(tenant, k, v)
    db.commit()
    db.refresh(tenant)
    return tenant
