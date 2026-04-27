"""MS-014 REST API — evaluation, health reports, synthetic management."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adapters.scoring.drift_detector import compute_health, save_snapshot
from app.application.use_cases.evaluate_feedback import evaluate
from app.application.use_cases.generate_synthetic import generate_batch_for_health_recovery
from app.config import settings
from app.models.evaluation import FeedbackEvaluation, ModelHealthSnapshot, SyntheticExample
from pec_shared.models_base import get_db

router = APIRouter(prefix="/api/v1/evaluator")


# ── Evaluation ────────────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    feedback_id: str
    observation_id: str
    ai_feedback: dict
    human_feedback: dict
    transcription_text: str = ""


class EvaluateResponse(BaseModel):
    feedback_id: str
    quality_score: float
    structural_score: float
    evidence_score: float
    delta_score: float
    guardrail_score: float
    semantic_score: float
    selection_weight: float
    details: dict


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_feedback(req: EvaluateRequest, db: Session = Depends(get_db)):
    rec = evaluate(
        db               = db,
        feedback_id      = req.feedback_id,
        observation_id   = req.observation_id,
        ai_feedback      = req.ai_feedback,
        human_feedback   = req.human_feedback,
        transcription_text = req.transcription_text,
    )
    return EvaluateResponse(
        feedback_id      = rec.feedback_id,
        quality_score    = rec.quality_score,
        structural_score = rec.structural_score,
        evidence_score   = rec.evidence_score,
        delta_score      = rec.delta_score,
        guardrail_score  = rec.guardrail_score,
        semantic_score   = rec.semantic_score,
        selection_weight = rec.selection_weight,
        details          = rec.details,
    )


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health-report")
def health_report(db: Session = Depends(get_db)):
    report = compute_health(db)
    # Retrieve last 5 snapshots for trend chart
    snapshots = (
        db.query(ModelHealthSnapshot)
        .order_by(ModelHealthSnapshot.snapshot_at.desc())
        .limit(10)
        .all()
    )
    return {
        "current": {
            "status":           report.status,
            "mean_quality":     report.mean_quality,
            "min_quality":      report.min_quality,
            "max_quality":      report.max_quality,
            "trend":            report.trend,
            "stddev":           report.stddev,
            "window_size":      report.window_size,
            "total_evaluated":  report.total_evaluated,
            "alert_triggered":  report.alert_triggered,
            "quality_threshold": settings.quality_alert_threshold,
        },
        "history": [
            {
                "snapshot_at":  s.snapshot_at.isoformat(),
                "mean_quality": s.mean_quality,
                "status":       s.status,
                "trend":        s.trend,
                "alert":        s.alert_triggered == "Y",
            }
            for s in reversed(snapshots)
        ],
    }


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total_evals = db.query(FeedbackEvaluation).count()
    total_syn   = db.query(SyntheticExample).filter_by(is_active="Y").count()
    last_eval = (
        db.query(FeedbackEvaluation)
        .order_by(FeedbackEvaluation.evaluated_at.desc())
        .first()
    )
    last_snap = (
        db.query(ModelHealthSnapshot)
        .order_by(ModelHealthSnapshot.snapshot_at.desc())
        .first()
    )

    # Score distribution bucketed in 0.1 steps
    from sqlalchemy import func, case
    dist = db.execute(
        __import__("sqlalchemy").text(
            """
            SELECT
              FLOOR(quality_score * 10) / 10 AS bucket,
              COUNT(*) AS cnt
            FROM feedback_evaluations
            GROUP BY bucket
            ORDER BY bucket
            """
        )
    ).fetchall()

    return {
        "total_evaluations":    total_evals,
        "active_synthetic":     total_syn,
        "last_evaluation_at":   last_eval.evaluated_at.isoformat() if last_eval else None,
        "last_snapshot_status": last_snap.status if last_snap else "no_data",
        "score_distribution":   [{"bucket": float(r[0]), "count": int(r[1])} for r in dist],
    }


# ── Synthetic management ──────────────────────────────────────────────────────

@router.post("/synthetic/generate", status_code=202)
def trigger_synthetic(db: Session = Depends(get_db)):
    count = generate_batch_for_health_recovery(db)
    return {"status": "completed", "examples_generated": count}


@router.get("/evaluations/{feedback_id}", response_model=EvaluateResponse)
def get_evaluation(feedback_id: str, db: Session = Depends(get_db)):
    rec = db.query(FeedbackEvaluation).filter_by(feedback_id=feedback_id).first()
    if not rec:
        raise HTTPException(404, "Evaluation not found")
    return EvaluateResponse(
        feedback_id      = rec.feedback_id,
        quality_score    = rec.quality_score,
        structural_score = rec.structural_score,
        evidence_score   = rec.evidence_score,
        delta_score      = rec.delta_score,
        guardrail_score  = rec.guardrail_score,
        semantic_score   = rec.semantic_score,
        selection_weight = rec.selection_weight,
        details          = rec.details,
    )
