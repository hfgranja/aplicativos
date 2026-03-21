from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json
import asyncio
from app.database import get_db
from app.models.finding import Finding
from app.models.execution import Execution
from app.models.user import User
from app.core.deps import get_current_user
from app.core.audit_logger import log_event
from app.schemas.finding import FindingOut, AcceptRiskRequest

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("", response_model=List[FindingOut])
def list_findings(execution_id: str = None, severity: str = None, engine: str = None,
                  is_resolved: bool = None, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    q = db.query(Finding).join(Execution).filter(Execution.tenant_id == current_user.tenant_id)
    if execution_id:
        q = q.filter(Finding.execution_id == execution_id)
    if severity:
        q = q.filter(Finding.severity == severity)
    if engine:
        q = q.filter(Finding.engine == engine)
    if is_resolved is not None:
        q = q.filter(Finding.is_resolved == is_resolved)
    return q.order_by(Finding.created_at.desc()).limit(500).all()


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(finding_id: str, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    finding = db.query(Finding).join(Execution).filter(
        Finding.id == finding_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.post("/{finding_id}/accept-risk")
def accept_risk(finding_id: str, body: AcceptRiskRequest, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    finding = db.query(Finding).join(Execution).filter(
        Finding.id == finding_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.is_accepted_risk = True
    finding.accepted_by = current_user.id
    finding.accepted_at = datetime.utcnow()
    finding.acceptance_justification = body.justification
    db.commit()
    log_event(db, "finding.risk_accepted", user_id=current_user.id, tenant_id=current_user.tenant_id,
              resource_type="finding", resource_id=finding_id,
              payload={"justification": body.justification})
    return {"detail": "Risk accepted"}


@router.post("/{finding_id}/resolve")
def resolve_finding(finding_id: str, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    finding = db.query(Finding).join(Execution).filter(
        Finding.id == finding_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.is_resolved = True
    finding.resolved_at = datetime.utcnow()
    db.commit()
    return {"detail": "Finding resolved"}


@router.post("/{finding_id}/fix")
def generate_fix(finding_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    finding = db.query(Finding).join(Execution).filter(
        Finding.id == finding_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    background_tasks.add_task(_generate_fix_async, finding_id)
    return {"detail": "Fix generation started", "finding_id": finding_id}


def _generate_fix_async(finding_id: str):
    from app.database import SessionLocal
    from app.services.fix_proposal_service import generate_fix_proposal
    db = SessionLocal()
    try:
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if finding:
            proposal = generate_fix_proposal(finding)
            if proposal:
                finding.fix_proposal = proposal
                db.commit()
    finally:
        db.close()


@router.get("/{finding_id}/fix-stream")
async def fix_stream(finding_id: str, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    finding = db.query(Finding).join(Execution).filter(
        Finding.id == finding_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    async def stream():
        from app.services.fix_proposal_service import stream_fix_proposal
        async for chunk in stream_fix_proposal(finding):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
