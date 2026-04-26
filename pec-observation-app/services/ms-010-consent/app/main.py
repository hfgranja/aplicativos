from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pec_shared.telemetry import init_telemetry

init_telemetry()

from .database import create_tables
from .adapters.api.consent_router import router as consent_router
from .adapters.events.redis_consumer import start_consumer
from .config import settings

app = FastAPI(title="PEC Consent & Retention Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(consent_router)


@app.on_event("startup")
def startup():
    create_tables()
    start_consumer(settings.REDIS_URL)
    _start_retention_scheduler()


def _start_retention_scheduler():
    """Background job to execute scheduled audio deletions."""
    import threading
    from datetime import datetime
    import boto3
    from botocore.config import Config
    import redis as redis_lib
    from .models.consent import DeletionSchedule
    from .database import SessionLocal
    from pec_shared.events import EventEnvelope, STREAM_CONSENT, publish_event
    from pec_shared.events import EVT_AUDIO_DELETED

    def _run():
        import time
        while True:
            time.sleep(3600)  # Check every hour
            db = SessionLocal()
            try:
                overdue = db.query(DeletionSchedule).filter(
                    DeletionSchedule.status == "SCHEDULED",
                    DeletionSchedule.scheduled_delete_at <= datetime.utcnow(),
                ).all()
                for schedule in overdue:
                    try:
                        client = boto3.client(
                            "s3",
                            endpoint_url=settings.MINIO_ENDPOINT,
                            aws_access_key_id=settings.MINIO_ROOT_USER,
                            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
                            config=Config(signature_version="s3v4"),
                            region_name="us-east-1",
                        )
                        client.delete_object(
                            Bucket=settings.MINIO_BUCKET_AUDIO,
                            Key=schedule.audio_minio_key,
                        )
                        schedule.status = "COMPLETED"
                        schedule.deleted_at = datetime.utcnow()
                        db.commit()

                        r = redis_lib.from_url(settings.REDIS_URL)
                        env = EventEnvelope.create(
                            event_type=EVT_AUDIO_DELETED,
                            producer="ms-010-consent",
                            payload={"observation_id": schedule.observation_id,
                                     "minio_key": schedule.audio_minio_key},
                            correlation_id=schedule.observation_id,
                        )
                        publish_event(r, STREAM_CONSENT, env)
                    except Exception as exc:
                        schedule.status = "FAILED"
                        schedule.failure_reason = str(exc)
                        db.commit()
            finally:
                db.close()

    t = threading.Thread(target=_run, daemon=True)
    t.start()


@app.get("/")
def root():
    return {"service": "pec-consent", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
