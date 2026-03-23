import csv
import json
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.execution import Execution
from app.models.finding import Finding
from app.models.release import ReleaseDecision
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{execution_id}")
def get_report(execution_id: str, format: str = Query("json", regex="^(json|csv)$"),
               db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ex = db.query(Execution).filter(
        Execution.id == execution_id, Execution.tenant_id == current_user.tenant_id
    ).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")

    findings = db.query(Finding).filter(Finding.execution_id == execution_id).all()
    release = db.query(ReleaseDecision).filter(ReleaseDecision.execution_id == execution_id).first()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "engine", "pyramid_level", "severity", "category", "title",
                         "file_path", "line_number", "cwe_id", "neural_score", "is_resolved"])
        for f in findings:
            writer.writerow([f.id, f.engine, f.pyramid_level, f.severity, f.category, f.title,
                             f.file_path, f.line_number, f.cwe_id, f.neural_score, f.is_resolved])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report_{execution_id}.csv"},
        )

    severity_counts = {}
    for f in findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    return JSONResponse({
        "execution": {
            "id": ex.id,
            "application_id": ex.application_id,
            "mode": ex.mode,
            "status": ex.status,
            "started_at": ex.started_at.isoformat() if ex.started_at else None,
            "finished_at": ex.finished_at.isoformat() if ex.finished_at else None,
            "pyramid_coverage": ex.pyramid_coverage,
        },
        "summary": {
            "total_findings": len(findings),
            "by_severity": severity_counts,
            "engines_run": ex.engines_run,
        },
        "release_decision": {
            "decision": release.decision if release else "PENDING",
            "score": release.score if release else None,
            "pyramid_coverage_summary": release.pyramid_coverage_summary if release else {},
        } if release else None,
        "findings": [
            {
                "id": f.id,
                "engine": f.engine,
                "pyramid_level": f.pyramid_level,
                "severity": f.severity,
                "category": f.category,
                "title": f.title,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "cwe_id": f.cwe_id,
                "neural_score": f.neural_score,
                "has_fix_proposal": f.fix_proposal is not None,
            }
            for f in findings
        ],
    })
