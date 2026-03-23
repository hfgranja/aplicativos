from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.execution import Execution, TestRun
from app.models.application import Application
from app.models.user import User
from app.core.deps import get_current_user
from app.core.audit_logger import log_event
from app.schemas.execution import ExecutionCreate, ExecutionOut, TestRunOut

router = APIRouter(prefix="/executions", tags=["executions"])

DEFAULT_ENGINES = {
    "FAST": ["sast", "contract", "security"],
    "FULL": ["sast", "property_based", "mutation", "contract", "regression", "fuzzing", "differential",
             "integration", "e2e", "performance", "security"],
    "REGULATORY": ["sast", "property_based", "mutation", "contract", "regression", "fuzzing",
                   "differential", "integration", "e2e", "performance", "security", "chaos"],
}


@router.post("", response_model=ExecutionOut)
def create_execution(body: ExecutionCreate, background_tasks: BackgroundTasks,
                     db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    app = db.query(Application).filter(
        Application.id == body.application_id,
        Application.tenant_id == current_user.tenant_id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    engines = body.engines or DEFAULT_ENGINES.get(body.mode, DEFAULT_ENGINES["FULL"])

    execution = Execution(
        tenant_id=current_user.tenant_id,
        application_id=body.application_id,
        mode=body.mode,
        triggered_by=current_user.id,
        pipeline_ref=body.pipeline_ref,
        commit_sha=body.commit_sha,
        engines_run=engines,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    log_event(db, "execution.created", user_id=current_user.id, tenant_id=current_user.tenant_id,
              resource_type="execution", resource_id=execution.id,
              payload={"mode": body.mode, "engines": engines})

    # Dispatch to Celery worker
    background_tasks.add_task(_dispatch_execution, execution.id)

    return execution


def _dispatch_execution(execution_id: str):
    try:
        from app.workers.tasks.orchestrator_task import run_execution
        run_execution.delay(execution_id)
    except Exception:
        pass  # Celery may not be available in dev without broker


@router.get("", response_model=List[ExecutionOut])
def list_executions(app_id: str = None, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    q = db.query(Execution).filter(Execution.tenant_id == current_user.tenant_id)
    if app_id:
        q = q.filter(Execution.application_id == app_id)
    return q.order_by(Execution.created_at.desc()).limit(100).all()


@router.get("/{execution_id}", response_model=ExecutionOut)
def get_execution(execution_id: str, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    ex = db.query(Execution).filter(
        Execution.id == execution_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ex


@router.get("/{execution_id}/test-runs", response_model=List[TestRunOut])
def get_test_runs(execution_id: str, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    ex = db.query(Execution).filter(
        Execution.id == execution_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return db.query(TestRun).filter(TestRun.execution_id == execution_id).all()


@router.post("/{execution_id}/cancel")
def cancel_execution(execution_id: str, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    ex = db.query(Execution).filter(
        Execution.id == execution_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    if ex.status not in ("PENDING", "RUNNING"):
        raise HTTPException(status_code=400, detail="Execution is not cancellable")
    ex.status = "CANCELLED"
    ex.finished_at = datetime.utcnow()
    db.commit()
    log_event(db, "execution.cancelled", user_id=current_user.id, tenant_id=current_user.tenant_id,
              resource_type="execution", resource_id=execution_id)
    return {"detail": "Execution cancelled"}


@router.post("/{execution_id}/rerun", response_model=ExecutionOut)
def rerun_execution(execution_id: str, background_tasks: BackgroundTasks,
                    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    original = db.query(Execution).filter(
        Execution.id == execution_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not original:
        raise HTTPException(status_code=404, detail="Execution not found")

    new_ex = Execution(
        tenant_id=original.tenant_id,
        application_id=original.application_id,
        mode=original.mode,
        triggered_by=current_user.id,
        engines_run=original.engines_run,
        commit_sha=original.commit_sha,
    )
    db.add(new_ex)
    db.commit()
    db.refresh(new_ex)
    background_tasks.add_task(_dispatch_execution, new_ex.id)
    return new_ex
