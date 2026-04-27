"""MS-014 Evaluator — model quality monitoring and synthetic augmentation."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from sqlalchemy import text

from app.adapters.api.router import router
from app.adapters.events.consumer import start_consumer
from app.adapters.scoring.drift_detector import compute_health, save_snapshot
from app.application.use_cases.evaluate_feedback import evaluate
from app.application.use_cases.generate_synthetic import generate_batch_for_health_recovery
from app.config import settings
from app.models.evaluation import FeedbackEvaluation, ModelHealthSnapshot, SyntheticExample
from pec_shared.models_base import Base, engine, SessionLocal
from pec_shared.telemetry import init_telemetry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ms-014")

app = FastAPI(title="PEC Evaluator", version="1.0.0")
app.include_router(router)

init_telemetry(settings.service_name, settings.environment, settings.otel_exporter_enabled)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")

    start_consumer(_handle_approval_event)

    scheduler = BackgroundScheduler()
    # Snapshot health every 6 hours
    scheduler.add_job(_scheduled_health_snapshot, trigger="interval", hours=6, id="health-snapshot")
    # Recovery run every morning at 03:00 if health is degraded
    scheduler.add_job(_scheduled_recovery, trigger="cron", hour=3, minute=0, id="recovery")
    scheduler.start()
    logger.info("Scheduler started")


def _handle_approval_event(payload: dict) -> None:
    """Called by the Redis consumer for each feedback.human_approved event."""
    feedback_id       = payload.get("feedback_id", "")
    observation_id    = payload.get("observation_id", "")
    ai_feedback       = payload.get("ai_feedback_draft", {})
    human_feedback    = payload.get("feedback_content", {})
    transcription     = payload.get("transcription_text", "")

    if not feedback_id or not ai_feedback or not human_feedback:
        logger.debug("Skipping event — missing feedback data (id=%s)", feedback_id)
        return

    db = SessionLocal()
    try:
        evaluate(
            db               = db,
            feedback_id      = feedback_id,
            observation_id   = observation_id,
            ai_feedback      = ai_feedback,
            human_feedback   = human_feedback,
            transcription_text = transcription,
        )
    finally:
        db.close()


def _scheduled_health_snapshot() -> None:
    db = SessionLocal()
    try:
        report = compute_health(db)
        save_snapshot(db, report)
        logger.info("Health snapshot: status=%s mean_quality=%.3f trend=%.3f",
                    report.status, report.mean_quality, report.trend)
    finally:
        db.close()


def _scheduled_recovery() -> None:
    db = SessionLocal()
    try:
        report = compute_health(db)
        if report.status in ("degraded", "declining"):
            logger.warning(
                "Recovery triggered: status=%s — generating synthetic examples",
                report.status,
            )
            count = generate_batch_for_health_recovery(db)
            logger.info("Recovery generated %d synthetic examples", count)
    finally:
        db.close()


@app.get("/health")
def health():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        report = compute_health(db)
        return {
            "status": "healthy",
            "service": "ms-014-evaluator",
            "model_health": report.status,
            "mean_quality": report.mean_quality,
        }
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}
    finally:
        db.close()
