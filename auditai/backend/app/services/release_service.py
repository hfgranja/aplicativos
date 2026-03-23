"""
Release decision service: GREEN / YELLOW / RED based on findings + policy.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.finding import Finding
from app.models.execution import Execution, TestRun
from app.models.release import ReleaseDecision
from app.models.policy import Policy
from app.core.audit_logger import log_event

PYRAMID_LEVELS = {1: "sast", 2: "mutation", 3: "fuzzing", 4: "integration",
                  5: "contract", 6: "differential", 7: "e2e", 8: "performance",
                  9: "security", 10: "chaos"}

DEFAULT_POLICY = {
    "block_on_severity": ["CRITICAL"],
    "warn_on_severity": ["HIGH"],
    "mutation_score_minimum": 60,
    "max_critical_findings": 0,
}


def compute_release_decision(db: Session, execution_id: str, decided_by: str) -> ReleaseDecision:
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    findings = db.query(Finding).filter(Finding.execution_id == execution_id).all()
    test_runs = db.query(TestRun).filter(TestRun.execution_id == execution_id).all()

    # Load policy
    policy = db.query(Policy).filter(
        Policy.application_id == execution.application_id, Policy.is_active == True
    ).first()
    rules = policy.rules if policy else DEFAULT_POLICY

    blocking = []
    risk_acceptances = []
    decision = "GREEN"

    # Check critical/high findings
    block_severities = rules.get("block_on_severity", ["CRITICAL"])
    warn_severities = rules.get("warn_on_severity", ["HIGH"])
    max_critical = rules.get("max_critical_findings", 0)

    critical_count = 0
    for f in findings:
        if f.is_accepted_risk:
            risk_acceptances.append({"finding_id": f.id, "severity": f.severity,
                                      "accepted_by": f.accepted_by, "accepted_at": str(f.accepted_at)})
            continue
        if f.severity in block_severities:
            blocking.append(f.id)
            critical_count += 1
            decision = "RED"
        elif f.severity in warn_severities and decision == "GREEN":
            decision = "YELLOW"

    if critical_count > max_critical:
        decision = "RED"

    # Check mutation score
    mutation_runs = [r for r in test_runs if r.engine == "mutation" and r.score is not None]
    mutation_score = mutation_runs[0].score if mutation_runs else None
    min_mutation = rules.get("mutation_score_minimum", 60)
    if mutation_score is not None and mutation_score < min_mutation:
        if decision == "GREEN":
            decision = "YELLOW"

    # Check required engines
    required_engines = rules.get("required_engines", [])
    engines_run = set(execution.engines_run or [])
    missing_required = [e for e in required_engines if e not in engines_run]
    if missing_required:
        decision = "RED"
        blocking.extend([f"required_engine_missing:{e}" for e in missing_required])

    # Pyramid coverage
    pyramid_coverage = {}
    for run in test_runs:
        if run.pyramid_level:
            pyramid_coverage[run.pyramid_level] = {
                "engine": run.engine,
                "status": run.status,
                "score": run.score,
            }

    # Overall score (weighted average of engine scores)
    scores = [r.score for r in test_runs if r.score is not None]
    overall_score = int(sum(scores) / len(scores)) if scores else 0

    rd = ReleaseDecision(
        execution_id=execution_id,
        decision=decision,
        score=overall_score,
        blocking_findings=blocking,
        risk_acceptances=risk_acceptances,
        pyramid_coverage_summary=pyramid_coverage,
        policy_id=policy.id if policy else None,
        decided_by=decided_by,
        decided_at=datetime.utcnow(),
    )
    db.add(rd)
    db.commit()
    db.refresh(rd)

    log_event(db, "release.decision_generated", user_id=decided_by,
              tenant_id=execution.tenant_id, resource_type="release",
              resource_id=rd.id, payload={"decision": decision, "score": overall_score})

    return rd
