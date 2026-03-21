"""
Execution service — creates and manages test executions.
"""
from sqlalchemy.orm import Session
from app.models.execution import Execution
from app.models.application import Application


def get_execution_summary(db: Session, execution_id: str) -> dict:
    from app.models.finding import Finding
    from sqlalchemy import func
    findings = db.query(Finding).filter(Finding.execution_id == execution_id).all()
    severity_counts = {}
    for f in findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
    return {
        "total_findings": len(findings),
        "by_severity": severity_counts,
    }
