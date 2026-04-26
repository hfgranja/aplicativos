from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError

from ...database import get_db
from ...models.audit_event import AuditEvent
from pec_shared.security import decode_token
from ...config import settings

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.get("/events")
def list_events(
    correlation_id: Optional[str] = None,
    event_type: Optional[str] = None,
    producer: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user=Depends(_get_user),
):
    q = db.query(AuditEvent)
    if correlation_id:
        q = q.filter(AuditEvent.correlation_id == correlation_id)
    if event_type:
        q = q.filter(AuditEvent.event_type == event_type)
    if producer:
        q = q.filter(AuditEvent.producer == producer)
    events = q.order_by(AuditEvent.ingested_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "event_id": e.event_id,
            "event_type": e.event_type,
            "occurred_at": e.occurred_at,
            "correlation_id": e.correlation_id,
            "producer": e.producer,
            "stream": e.stream,
            "payload": e.payload,
            "ingested_at": e.ingested_at,
        }
        for e in events
    ]
