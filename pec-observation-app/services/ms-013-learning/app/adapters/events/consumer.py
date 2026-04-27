"""Redis Streams consumer — ingests knowledge and feedback events for learning."""
import json
import logging
import threading

import redis as redis_lib

from app.config import settings

logger = logging.getLogger(__name__)

# Streams this service listens on
STREAMS = {
    "pec.knowledge.events":    "ms-013-learning-knowledge",
    "pec.feedback.events":     "ms-013-learning-feedback",
    "pec.best_practices.events": "ms-013-learning-bp",
}


def _ensure_groups(r: redis_lib.Redis) -> None:
    for stream, group in STREAMS.items():
        try:
            r.xgroup_create(stream, group, id="0", mkstream=True)
        except redis_lib.exceptions.ResponseError:
            pass  # group already exists


def start_consumer(ingest_fn) -> None:
    """Start a background thread that feeds events to *ingest_fn(event_type, payload)*."""

    def _loop():
        r = redis_lib.from_url(settings.redis_url, decode_responses=True)
        _ensure_groups(r)
        consumer_name = "ms-013-instance-1"

        while True:
            try:
                entries = r.xreadgroup(
                    groupname=None,  # handled per-stream below
                    consumername=consumer_name,
                    streams={s: ">" for s in STREAMS},
                    count=10,
                    block=5000,
                )
                # entries is None when block times out with no messages
                if not entries:
                    continue

                for stream_name, messages in entries:
                    group = STREAMS.get(stream_name, "ms-013-learning-unknown")
                    for msg_id, fields in messages:
                        try:
                            event_type = fields.get("event_type", "")
                            payload = json.loads(fields.get("payload", "{}"))
                            ingest_fn(event_type, payload)
                            r.xack(stream_name, group, msg_id)
                        except Exception as exc:
                            logger.error(
                                "Error processing event %s from %s: %s",
                                msg_id, stream_name, exc,
                            )
            except Exception as exc:
                logger.warning("Consumer loop error (will retry): %s", exc)

    t = threading.Thread(target=_loop, daemon=True, name="learning-consumer")
    t.start()
    logger.info("Learning event consumer started")
