"""Redis Streams consumer for MS-014: listens on pec.feedback.events."""
import json
import logging
import threading

import redis as redis_lib

from app.config import settings

logger = logging.getLogger(__name__)

STREAM = "pec.feedback.events"
GROUP  = "ms-014-evaluator"


def _ensure_group(r: redis_lib.Redis) -> None:
    try:
        r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except redis_lib.exceptions.ResponseError:
        pass


def start_consumer(evaluate_fn) -> None:
    """Background thread that calls *evaluate_fn(payload)* on approval events."""

    def _loop():
        r = redis_lib.from_url(settings.redis_url, decode_responses=True)
        _ensure_group(r)
        consumer = "ms-014-instance-1"

        while True:
            try:
                entries = r.xreadgroup(
                    groupname=GROUP,
                    consumername=consumer,
                    streams={STREAM: ">"},
                    count=5,
                    block=5000,
                )
                if not entries:
                    continue
                for _, messages in entries:
                    for msg_id, fields in messages:
                        event_type = fields.get("event_type", "")
                        if event_type == "feedback.human_approved":
                            try:
                                payload = json.loads(fields.get("payload", "{}"))
                                evaluate_fn(payload)
                            except Exception as exc:
                                logger.error("Evaluation error for msg %s: %s", msg_id, exc)
                        r.xack(STREAM, GROUP, msg_id)
            except Exception as exc:
                logger.warning("Consumer error (retrying): %s", exc)

    t = threading.Thread(target=_loop, daemon=True, name="evaluator-consumer")
    t.start()
    logger.info("Evaluator consumer started on stream %s", STREAM)
