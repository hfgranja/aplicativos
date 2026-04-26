"""Consent service — consumes audio.uploaded events to schedule deletion."""
import logging
import threading
from datetime import datetime, timedelta

import redis as redis_lib

from pec_shared.events import (
    STREAM_AUDIO, EVT_AUDIO_UPLOADED,
    consume_events, ack_event,
)
from ...database import SessionLocal
from ...models.consent import DeletionSchedule
from ...config import settings

logger = logging.getLogger(__name__)
CONSUMER_GROUP = "consent-service"
CONSUMER_NAME = "consent-worker-1"

_stop_event = threading.Event()


def _schedule_deletion(payload: dict) -> None:
    observation_id = payload.get("observation_id", "")
    minio_key = payload.get("minio_key", "")
    if not minio_key:
        return

    db = SessionLocal()
    try:
        existing = db.query(DeletionSchedule).filter(
            DeletionSchedule.observation_id == observation_id
        ).first()
        if existing:
            return

        scheduled_at = datetime.utcnow() + timedelta(days=settings.AUDIO_RETENTION_DAYS)
        schedule = DeletionSchedule(
            observation_id=observation_id,
            audio_minio_key=minio_key,
            scheduled_delete_at=scheduled_at,
            status="SCHEDULED",
        )
        db.add(schedule)
        db.commit()
        logger.info("Audio deletion scheduled for observation %s at %s",
                    observation_id, scheduled_at.isoformat())
    except Exception as exc:
        logger.error("Error scheduling deletion for %s: %s", observation_id, exc)
    finally:
        db.close()


def _run_consumer(redis_url: str) -> None:
    r = redis_lib.from_url(redis_url)
    logger.info("Consent consumer started.")
    while not _stop_event.is_set():
        try:
            messages = consume_events(r, STREAM_AUDIO, CONSUMER_GROUP, CONSUMER_NAME,
                                      count=10, block_ms=2000)
            for msg_id, envelope in messages:
                if envelope.event_type == EVT_AUDIO_UPLOADED:
                    _schedule_deletion(envelope.payload)
                ack_event(r, STREAM_AUDIO, CONSUMER_GROUP, msg_id)
        except Exception as exc:
            logger.warning("Consent consumer error: %s", exc)


def start_consumer(redis_url: str) -> threading.Thread:
    t = threading.Thread(target=_run_consumer, args=(redis_url,), daemon=True)
    t.start()
    return t
