from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent


def log_event(
    db: Session,
    action: str,
    user_id: str = None,
    tenant_id: str = None,
    resource_type: str = None,
    resource_id: str = None,
    payload: dict = None,
    ip_address: str = None,
    user_agent: str = None,
):
    event = AuditEvent(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload or {},
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    return event
