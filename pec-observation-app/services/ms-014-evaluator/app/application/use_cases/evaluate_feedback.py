"""Evaluate one AI feedback vs. human-approved version and persist result.

Also propagates quality score to MS-013 so Modelfile selection is weighted.
"""
from __future__ import annotations

import math
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.adapters.scoring.quality_scorer import score as compute_score
from app.adapters.scoring.drift_detector import compute_health, save_snapshot
from app.config import settings
from app.models.evaluation import FeedbackEvaluation

logger = logging.getLogger(__name__)


def _recency_weight(evaluated_at: datetime) -> float:
    """Exponential decay: weight = exp(-days / half_life)."""
    now = datetime.now(timezone.utc)
    if evaluated_at.tzinfo is None:
        evaluated_at = evaluated_at.replace(tzinfo=timezone.utc)
    days = max(0.0, (now - evaluated_at).total_seconds() / 86400)
    return math.exp(-days * math.log(2) / settings.recency_half_life_days)


def evaluate(
    db: Session,
    feedback_id: str,
    observation_id: str,
    ai_feedback: dict,
    human_feedback: dict,
    transcription_text: str = "",
) -> FeedbackEvaluation:
    report = compute_score(
        ai_feedback    = ai_feedback,
        human_feedback = human_feedback,
        ollama_base_url    = settings.ollama_base_url,
        embedding_model    = settings.ollama_embedding_model,
        compute_semantic   = True,
    )

    recency = _recency_weight(datetime.now(timezone.utc))
    selection_weight = report.quality_score * 0.70 + recency * 0.30

    existing = db.query(FeedbackEvaluation).filter_by(feedback_id=feedback_id).first()
    if existing:
        existing.structural_score  = report.structural_score
        existing.evidence_score    = report.evidence_score
        existing.delta_score       = report.delta_score
        existing.guardrail_score   = report.guardrail_score
        existing.semantic_score    = report.semantic_score
        existing.quality_score     = report.quality_score
        existing.selection_weight  = round(selection_weight, 4)
        existing.details           = report.details
        existing.evaluated_at      = datetime.now(timezone.utc)
        db.commit()
        rec = existing
    else:
        rec = FeedbackEvaluation(
            feedback_id       = feedback_id,
            observation_id    = observation_id,
            structural_score  = report.structural_score,
            evidence_score    = report.evidence_score,
            delta_score       = report.delta_score,
            guardrail_score   = report.guardrail_score,
            semantic_score    = report.semantic_score,
            quality_score     = report.quality_score,
            selection_weight  = round(selection_weight, 4),
            details           = report.details,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

    logger.info(
        "Evaluated feedback %s: quality=%.3f (struct=%.2f evid=%.2f delta=%.2f "
        "guard=%.2f sem=%.2f) weight=%.3f",
        feedback_id, report.quality_score,
        report.structural_score, report.evidence_score, report.delta_score,
        report.guardrail_score, report.semantic_score, selection_weight,
    )

    # Push quality score to MS-013 so it can weight example selection
    _notify_learning_engine(
        feedback_id      = feedback_id,
        quality_score    = report.quality_score,
        selection_weight = round(selection_weight, 4),
        transcription_text = transcription_text,
        human_feedback   = human_feedback,
    )

    # Compute and snapshot model health after every evaluation
    health = compute_health(db)
    save_snapshot(db, health)

    # If model is degraded, trigger synthetic augmentation
    if health.status == "degraded":
        logger.warning("Model degraded — requesting synthetic augmentation from MS-014 background")
        _trigger_synthetic(db, feedback_id)

    return rec


def _notify_learning_engine(
    feedback_id: str,
    quality_score: float,
    selection_weight: float,
    transcription_text: str,
    human_feedback: dict,
) -> None:
    """Tell MS-013 the quality score so it can weight this example in Modelfile builds."""
    url = settings.learning_service_url
    try:
        httpx.patch(
            f"{url}/api/v1/learning/examples/{feedback_id}/weight",
            json={"quality_score": quality_score, "selection_weight": selection_weight},
            timeout=5.0,
        )
    except Exception as exc:
        logger.debug("Could not update weight in MS-013: %s", exc)


def _trigger_synthetic(db: Session, anchor_feedback_id: str) -> None:
    """Background call — request MS-014 itself to generate synthetic examples."""
    try:
        from app.application.use_cases.generate_synthetic import generate_for_feedback
        generate_for_feedback(db, anchor_feedback_id)
    except Exception as exc:
        logger.warning("Synthetic generation error: %s", exc)
