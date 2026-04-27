"""Model health / drift detection from a rolling window of quality scores.

Health status:
  improving  — mean quality trending upward  (trend > +0.03)
  stable     — mean quality within ±0.03 of previous window
  declining  — mean quality trending down    (trend < -0.03)
  degraded   — mean quality below alert threshold (e.g. 0.60)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean, stdev

from sqlalchemy.orm import Session

from app.config import settings
from app.models.evaluation import FeedbackEvaluation, ModelHealthSnapshot

logger = logging.getLogger(__name__)


@dataclass
class HealthReport:
    status: str           # improving | stable | declining | degraded
    mean_quality: float
    min_quality: float
    max_quality: float
    trend: float          # current_mean - prev_mean
    window_size: int
    total_evaluated: int
    alert_triggered: bool
    stddev: float


def compute_health(db: Session) -> HealthReport:
    window = settings.health_window
    rows = (
        db.query(FeedbackEvaluation.quality_score, FeedbackEvaluation.evaluated_at)
        .order_by(FeedbackEvaluation.evaluated_at.desc())
        .limit(window * 2)
        .all()
    )

    total = db.query(FeedbackEvaluation).count()

    if not rows:
        return HealthReport("stable", 0.0, 0.0, 0.0, 0.0, 0, total, False, 0.0)

    current_scores = [r[0] for r in rows[:window]]
    prev_scores    = [r[0] for r in rows[window:window * 2]]

    cur_mean = mean(current_scores)
    prev_mean = mean(prev_scores) if prev_scores else cur_mean
    trend = cur_mean - prev_mean

    if cur_mean < settings.quality_alert_threshold:
        status = "degraded"
    elif trend > 0.03:
        status = "improving"
    elif trend < -0.03:
        status = "declining"
    else:
        status = "stable"

    alert = status == "degraded"
    if alert:
        logger.warning(
            "MODEL HEALTH ALERT: quality=%.3f below threshold=%.3f",
            cur_mean, settings.quality_alert_threshold,
        )

    return HealthReport(
        status          = status,
        mean_quality    = round(cur_mean, 4),
        min_quality     = round(min(current_scores), 4),
        max_quality     = round(max(current_scores), 4),
        trend           = round(trend, 4),
        window_size     = len(current_scores),
        total_evaluated = total,
        alert_triggered = alert,
        stddev          = round(stdev(current_scores) if len(current_scores) > 1 else 0.0, 4),
    )


def save_snapshot(db: Session, report: HealthReport) -> ModelHealthSnapshot:
    snap = ModelHealthSnapshot(
        window_size     = report.window_size,
        mean_quality    = report.mean_quality,
        min_quality     = report.min_quality,
        max_quality     = report.max_quality,
        trend           = report.trend,
        status          = report.status,
        total_evaluated = report.total_evaluated,
        alert_triggered = "Y" if report.alert_triggered else "N",
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap
