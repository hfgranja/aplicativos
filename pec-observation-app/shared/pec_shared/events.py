"""Event envelope and Redis Streams helpers for inter-service communication."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    event_version: str
    occurred_at: str
    correlation_id: str
    causation_id: str
    tenant_id: str
    producer: str
    payload: dict[str, Any]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["payload"] = json.dumps(self.payload)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "EventEnvelope":
        payload = d.get("payload", "{}")
        if isinstance(payload, (bytes, str)):
            payload = json.loads(payload)
        return cls(
            event_id=d["event_id"],
            event_type=d["event_type"],
            event_version=d.get("event_version", "1.0"),
            occurred_at=d["occurred_at"],
            correlation_id=d.get("correlation_id", ""),
            causation_id=d.get("causation_id", ""),
            tenant_id=d.get("tenant_id", "default"),
            producer=d.get("producer", "unknown"),
            payload=payload,
        )

    @classmethod
    def create(
        cls,
        event_type: str,
        producer: str,
        payload: dict[str, Any],
        correlation_id: str = "",
        causation_id: str = "",
        tenant_id: str = "default",
        event_version: str = "1.0",
    ) -> "EventEnvelope":
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            event_version=event_version,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id,
            causation_id=causation_id,
            tenant_id=tenant_id,
            producer=producer,
            payload=payload,
        )


# ─── Stream names ──────────────────────────────────────────────
STREAM_IDENTITY = "pec.identity.events"
STREAM_SCHOOL = "pec.school.events"
STREAM_OBSERVATION = "pec.observation.events"
STREAM_AUDIO = "pec.audio.events"
STREAM_TRANSCRIPTION = "pec.transcription.events"
STREAM_AI_FEEDBACK = "pec.ai_feedback.events"
STREAM_FEEDBACK = "pec.feedback.events"
STREAM_PDF = "pec.pdf.events"
STREAM_CONSENT = "pec.consent.events"

ALL_STREAMS = [
    STREAM_IDENTITY, STREAM_SCHOOL, STREAM_OBSERVATION, STREAM_AUDIO,
    STREAM_TRANSCRIPTION, STREAM_AI_FEEDBACK, STREAM_FEEDBACK, STREAM_PDF,
    STREAM_CONSENT,
]

# ─── Event types ───────────────────────────────────────────────
# Identity
EVT_USER_LOGGED_IN = "user.logged_in"
EVT_USER_LOGGED_OUT = "user.logged_out"

# School
EVT_SCHOOL_CREATED = "school.created"
EVT_SCHOOL_UPDATED = "school.updated"
EVT_TEACHER_CREATED = "teacher.created"
EVT_TEACHER_UPDATED = "teacher.updated"

# Observation
EVT_OBSERVATION_CREATED = "observation.created"
EVT_OBSERVATION_UPDATED = "observation.updated"
EVT_OBSERVATION_STATUS_CHANGED = "observation.status_changed"

# Audio
EVT_AUDIO_UPLOAD_REQUESTED = "audio.upload_requested"
EVT_AUDIO_UPLOADED = "audio.uploaded"
EVT_AUDIO_VALIDATED = "audio.validated"
EVT_AUDIO_REJECTED = "audio.rejected"
EVT_AUDIO_DELETED = "audio.deleted"

# Transcription
EVT_TRANSCRIPTION_STARTED = "transcription.started"
EVT_TRANSCRIPTION_COMPLETED = "transcription.completed"
EVT_TRANSCRIPTION_FAILED = "transcription.failed"

# AI Feedback
EVT_AI_FEEDBACK_STARTED = "ai_feedback.started"
EVT_AI_FEEDBACK_GENERATED = "ai_feedback.generated"
EVT_AI_FEEDBACK_FAILED = "ai_feedback.failed"

# Feedback
EVT_FEEDBACK_CREATED = "feedback.created"
EVT_FEEDBACK_EDITED = "feedback.edited"
EVT_FEEDBACK_HUMAN_REVIEWED = "feedback.human_reviewed"
EVT_FEEDBACK_APPROVED = "feedback.approved"

# PDF
EVT_PDF_GENERATION_REQUESTED = "pdf.generation_requested"
EVT_PDF_GENERATED = "pdf.generated"
EVT_PDF_GENERATION_FAILED = "pdf.generation_failed"

# Consent
EVT_CONSENT_RECORDED = "consent.recorded"
EVT_AUDIO_DELETION_REQUESTED = "audio.deletion_requested"


# ─── Redis Streams helpers ─────────────────────────────────────

def _ensure_group(redis_client, stream: str, group: str) -> None:
    try:
        redis_client.xgroup_create(stream, group, id="0", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def publish_event(redis_client, stream: str, envelope: EventEnvelope) -> str:
    """Append an event to a Redis Stream. Returns the message ID."""
    return redis_client.xadd(stream, envelope.to_dict())


def consume_events(
    redis_client,
    stream: str,
    group: str,
    consumer: str,
    count: int = 10,
    block_ms: int = 2000,
) -> list[tuple[str, EventEnvelope]]:
    """Read pending events from a consumer group. Returns [(msg_id, envelope)]."""
    _ensure_group(redis_client, stream, group)
    messages = redis_client.xreadgroup(
        groupname=group,
        consumername=consumer,
        streams={stream: ">"},
        count=count,
        block=block_ms,
    )
    result = []
    if messages:
        for _stream, entries in messages:
            for msg_id, data in entries:
                # Redis returns bytes keys; decode them
                decoded = {
                    k.decode() if isinstance(k, bytes) else k: v
                    for k, v in data.items()
                }
                result.append((msg_id, EventEnvelope.from_dict(decoded)))
    return result


def ack_event(redis_client, stream: str, group: str, message_id) -> None:
    redis_client.xack(stream, group, message_id)
