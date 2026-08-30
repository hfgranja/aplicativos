"""LGPD — Data Subject Access Request (DSAR) endpoint.

Implements Articles 18-20 of Lei 13.709/2018 (LGPD):
  - Art. 18 I: access to data (GET /dsar/access)
  - Art. 18 VI: deletion of data (POST /dsar/delete)
  - Art. 18 VII/VIII: portability + objection (extensible)
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import Session

from ...database import SessionLocal, get_db
from ...models.consent import ConsentRecord, DeletionSchedule
from pec_shared.models_base import Base, gen_uuid
from pec_shared.security import decode_token
from ...config import settings

router = APIRouter(prefix="/api/v1/dsar", tags=["dsar"])


class DSARStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class DSARRequest(Base):
    __tablename__ = "dsar_requests"

    id = Column(String, primary_key=True, default=gen_uuid)
    requester_user_id = Column(String, nullable=False, index=True)
    request_type = Column(String, nullable=False)  # ACCESS | DELETE | PORTABILITY
    status = Column(String, nullable=False, default=DSARStatus.PENDING)
    legal_basis = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    result_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


def _get_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class DSARAccessRequest(BaseModel):
    notes: Optional[str] = None


class DSARDeleteRequest(BaseModel):
    legal_basis: str = "LGPD Art. 18 VI"
    notes: Optional[str] = None


class DSARResponse(BaseModel):
    id: str
    request_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None

    class Config:
        from_attributes = True


class DataExport(BaseModel):
    user_id: str
    export_timestamp: datetime
    consents: list
    deletion_schedules: list


@router.post("/access", response_model=DSARResponse, status_code=201)
def request_access(
    body: DSARAccessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(_get_user),
):
    """LGPD Art. 18 I — Request export of all personal data held on the user."""
    user_id = user.get("sub", "")
    req = DSARRequest(
        requester_user_id=user_id,
        request_type="ACCESS",
        notes=body.notes,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    background_tasks.add_task(_fulfil_access_request, req.id, user_id)
    return req


@router.post("/delete", response_model=DSARResponse, status_code=201)
def request_deletion(
    body: DSARDeleteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(_get_user),
):
    """LGPD Art. 18 VI — Request deletion of all personal data."""
    user_id = user.get("sub", "")
    req = DSARRequest(
        requester_user_id=user_id,
        request_type="DELETE",
        legal_basis=body.legal_basis,
        notes=body.notes,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    background_tasks.add_task(_fulfil_deletion_request, req.id, user_id)
    return req


@router.get("/{request_id}", response_model=DSARResponse)
def get_dsar_status(
    request_id: str,
    db: Session = Depends(get_db),
    user=Depends(_get_user),
):
    """Check the status of a DSAR request."""
    user_id = user.get("sub", "")
    req = db.query(DSARRequest).filter(DSARRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.requester_user_id != user_id and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return req


@router.get("", response_model=List[DSARResponse])
def list_my_requests(
    db: Session = Depends(get_db),
    user=Depends(_get_user),
):
    """List all DSAR requests made by the authenticated user."""
    user_id = user.get("sub", "")
    return db.query(DSARRequest).filter(
        DSARRequest.requester_user_id == user_id
    ).order_by(DSARRequest.created_at.desc()).all()


def _fulfil_access_request(request_id: str, user_id: str) -> None:
    db = SessionLocal()
    try:
        req = db.query(DSARRequest).filter(DSARRequest.id == request_id).first()
        if not req:
            return
        req.status = DSARStatus.IN_PROGRESS
        db.commit()

        consents = db.query(ConsentRecord).filter(
            ConsentRecord.accepted_by_user_id == user_id
        ).all()
        schedules = db.query(DeletionSchedule).all()

        export = {
            "user_id": user_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "consents": [
                {
                    "id": c.id,
                    "observation_id": c.observation_id,
                    "consent_type": c.consent_type,
                    "accepted_at": c.accepted_at.isoformat(),
                    "version": c.version,
                }
                for c in consents
            ],
            "deletion_schedules": [
                {
                    "id": s.id,
                    "observation_id": s.observation_id,
                    "scheduled_delete_at": s.scheduled_delete_at.isoformat(),
                    "status": s.status,
                }
                for s in schedules
                if any(c.observation_id == s.observation_id for c in consents)
            ],
        }

        req.status = DSARStatus.COMPLETED
        req.completed_at = datetime.utcnow()
        req.notes = str(export)
        db.commit()
    except Exception as exc:
        try:
            req = db.query(DSARRequest).filter(DSARRequest.id == request_id).first()
            if req:
                req.status = DSARStatus.REJECTED
                req.notes = f"Error: {exc}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _fulfil_deletion_request(request_id: str, user_id: str) -> None:
    """Mark user consent records as deleted — audio files handled by existing retention scheduler."""
    db = SessionLocal()
    try:
        req = db.query(DSARRequest).filter(DSARRequest.id == request_id).first()
        if not req:
            return
        req.status = DSARStatus.IN_PROGRESS
        db.commit()

        consents = db.query(ConsentRecord).filter(
            ConsentRecord.accepted_by_user_id == user_id
        ).all()
        for c in consents:
            c.accepted_by_user_id = "DELETED"
            c.ip_address = None
            c.user_agent = None
        db.commit()

        req.status = DSARStatus.COMPLETED
        req.completed_at = datetime.utcnow()
        req.notes = f"Anonymised {len(consents)} consent record(s). Audio files follow 7-day retention schedule."
        db.commit()
    except Exception as exc:
        try:
            req = db.query(DSARRequest).filter(DSARRequest.id == request_id).first()
            if req:
                req.status = DSARStatus.REJECTED
                req.notes = f"Error: {exc}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
