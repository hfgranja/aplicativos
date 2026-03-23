from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.audit import AuditEvent
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventOut:
    pass


from pydantic import BaseModel


class AuditEventSchema(BaseModel):
    id: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    payload: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=List[AuditEventSchema])
def query_audit_log(
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AuditEvent).filter(AuditEvent.tenant_id == current_user.tenant_id)
    if action:
        q = q.filter(AuditEvent.action == action)
    if user_id:
        q = q.filter(AuditEvent.user_id == user_id)
    if resource_type:
        q = q.filter(AuditEvent.resource_type == resource_type)
    if resource_id:
        q = q.filter(AuditEvent.resource_id == resource_id)
    if since:
        q = q.filter(AuditEvent.created_at >= since)
    if until:
        q = q.filter(AuditEvent.created_at <= until)
    return q.order_by(AuditEvent.created_at.desc()).limit(limit).all()
