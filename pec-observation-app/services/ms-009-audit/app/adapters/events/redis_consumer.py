"""Audit service Redis Streams consumer — ingests ALL event streams."""
import asyncio
import logging
import threading

import redis as redis_lib
from pec_shared.events import (
    ALL_STREAMS, consume_events, ack_event, EventEnvelope,
)
from ...database import SessionLocal
from ...models.audit_event import AuditEvent

logger = logging.getLogger(__name__)
CONSUMER_GROUP = "audit-service"
CONSUMER_NAME = "audit-worker-1"

_stop_event = threading.Event()


def _ingest(envelope: EventEnvelope, stream: str, session) -> None:
    existing = session.query(AuditEvent).filter(
        AuditEvent.event_id == envelope.event_id
    ).first()
    if existing:
        return  # Idempotent
    record = AuditEvent(
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        event_version=envelope.event_version,
        occurred_at=envelope.occurred_at,
        correlation_id=envelope.correlation_id,
        causation_id=envelope.causation_id,
        tenant_id=envelope.tenant_id,
        producer=envelope.producer,
        payload=envelope.payload,
        stream=stream,
    )
    session.add(record)
    session.commit()


def _run_consumer(redis_url: str) -> None:
    r = redis_lib.from_url(redis_url)
    logger.info("Audit consumer started — watching %d streams", len(ALL_STREAMS))
    while not _stop_event.is_set():
        for stream in ALL_STREAMS:
            try:
                messages = consume_events(r, stream, CONSUMER_GROUP, CONSUMER_NAME,
                                          count=50, block_ms=500)
                if messages:
                    db = SessionLocal()
                    try:
                        for msg_id, envelope in messages:
                            _ingest(envelope, stream, db)
                            ack_event(r, stream, CONSUMER_GROUP, msg_id)
                    finally:
                        db.close()
            except Exception as exc:
                logger.warning("Audit consumer error on %s: %s", stream, exc)


def start_consumer(redis_url: str) -> threading.Thread:
    t = threading.Thread(target=_run_consumer, args=(redis_url,), daemon=True)
    t.start()
    return t


def stop_consumer() -> None:
    _stop_event.set()
