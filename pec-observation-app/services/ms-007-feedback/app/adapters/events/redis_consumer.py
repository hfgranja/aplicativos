"""Feedback service — consumes ai_feedback.generated events."""
import logging
import threading

import redis as redis_lib

from pec_shared.events import (
    STREAM_AI_FEEDBACK, STREAM_FEEDBACK,
    EVT_AI_FEEDBACK_GENERATED, EVT_FEEDBACK_CREATED,
    EventEnvelope, consume_events, ack_event, publish_event,
)
from ...database import SessionLocal
from ...models.feedback import Feedback

logger = logging.getLogger(__name__)
CONSUMER_GROUP = "feedback-service"
CONSUMER_NAME = "feedback-worker-1"

_stop_event = threading.Event()


def _process_ai_feedback_generated(payload: dict, r) -> None:
    observation_id = payload.get("observation_id", "")
    ai_feedback_id = payload.get("feedback_id", "")

    db = SessionLocal()
    try:
        existing = db.query(Feedback).filter(
            Feedback.observation_id == observation_id
        ).first()
        if existing:
            return  # Already created

        fb = Feedback(
            observation_id=observation_id,
            status="DRAFT",
            version=1,
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

        env = EventEnvelope.create(
            event_type=EVT_FEEDBACK_CREATED,
            producer="ms-007-feedback",
            payload={"feedback_id": fb.id, "observation_id": observation_id,
                     "status": "DRAFT"},
            correlation_id=observation_id,
            causation_id=ai_feedback_id,
        )
        publish_event(r, STREAM_FEEDBACK, env)
        logger.info("Feedback created for observation %s", observation_id)
    except Exception as exc:
        logger.error("Error creating feedback for %s: %s", observation_id, exc)
    finally:
        db.close()


def _run_consumer(redis_url: str) -> None:
    r = redis_lib.from_url(redis_url)
    logger.info("Feedback consumer started.")
    while not _stop_event.is_set():
        try:
            messages = consume_events(r, STREAM_AI_FEEDBACK, CONSUMER_GROUP, CONSUMER_NAME,
                                      count=10, block_ms=2000)
            for msg_id, envelope in messages:
                if envelope.event_type == EVT_AI_FEEDBACK_GENERATED:
                    _process_ai_feedback_generated(envelope.payload, r)
                ack_event(r, STREAM_AI_FEEDBACK, CONSUMER_GROUP, msg_id)
        except Exception as exc:
            logger.warning("Feedback consumer error: %s", exc)


def start_consumer(redis_url: str) -> threading.Thread:
    t = threading.Thread(target=_run_consumer, args=(redis_url,), daemon=True)
    t.start()
    return t
