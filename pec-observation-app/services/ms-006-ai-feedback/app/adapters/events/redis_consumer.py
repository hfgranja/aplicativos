"""AI Feedback service — consumes transcription.completed events."""
import logging
import threading

import redis as redis_lib

from pec_shared.events import (
    STREAM_TRANSCRIPTION, STREAM_AI_FEEDBACK,
    EVT_TRANSCRIPTION_COMPLETED, EVT_AI_FEEDBACK_STARTED,
    EVT_AI_FEEDBACK_GENERATED, EVT_AI_FEEDBACK_FAILED,
    EventEnvelope, consume_events, ack_event, publish_event,
)
from ...database import SessionLocal
from ...models.ai_feedback import AIFeedback
from ...config import settings

logger = logging.getLogger(__name__)
CONSUMER_GROUP = "ai-feedback-service"
CONSUMER_NAME = "ai-feedback-worker-1"

_stop_event = threading.Event()

REQUIRED_KEYS = {"summary", "strengths", "improvement_points", "evidence",
                 "suggested_action_plan"}


def _validate_ai_response(response: dict) -> None:
    for key in REQUIRED_KEYS:
        if key not in response:
            raise ValueError(f"Missing required key in AI response: {key}")
    # Safety guardrails
    text = str(response)
    forbidden = ["incompetente", "irresponsável", "falhou completamente"]
    for term in forbidden:
        if term.lower() in text.lower():
            raise ValueError(f"AI response contains forbidden term: {term}")


def _process_transcription_completed(payload: dict, r) -> None:
    observation_id = payload.get("observation_id", "")
    transcription_id = payload.get("transcription_id", "")

    db = SessionLocal()
    try:
        existing = db.query(AIFeedback).filter(
            AIFeedback.observation_id == observation_id
        ).first()
        if existing and existing.status == "COMPLETED":
            return

        if not existing:
            fb = AIFeedback(
                observation_id=observation_id,
                transcription_id=transcription_id,
                status="PROCESSING",
                model_provider=settings.LLM_PROVIDER,
                model_name=settings.OLLAMA_MODEL,
            )
            db.add(fb)
            db.commit()
            db.refresh(fb)
        else:
            fb = existing
            fb.status = "PROCESSING"
            db.commit()

        env = EventEnvelope.create(
            event_type=EVT_AI_FEEDBACK_STARTED,
            producer="ms-006-ai-feedback",
            payload={"feedback_id": fb.id, "observation_id": observation_id},
            correlation_id=observation_id,
        )
        publish_event(r, STREAM_AI_FEEDBACK, env)

        # Fetch transcription text from DB (same DB host, different DB)
        # In production, use MS-005 API. For MVP, query transcription DB directly via env.
        # We'll use a simplified approach: fetch text from the payload if available,
        # otherwise use a placeholder that works for dev.
        transcription_text = payload.get("full_text", "")
        if not transcription_text:
            # Fetch via HTTP from transcription service in production
            transcription_text = "(transcrição não disponível no payload)"

        observation_context = {
            "observation_id": observation_id,
            "language": payload.get("language", "pt-BR"),
            "segment_count": payload.get("segment_count", 0),
        }

        from ...adapters.llm.ollama_adapter import generate_feedback
        result = generate_feedback(
            transcription_text=transcription_text,
            observation_context=observation_context,
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )
        _validate_ai_response(result)

        from datetime import datetime
        fb.summary = result.get("summary", "")
        fb.strengths = result.get("strengths", [])
        fb.improvement_points = result.get("improvement_points", [])
        fb.evidence = result.get("evidence", [])
        fb.suggested_action_plan = result.get("suggested_action_plan", [])
        fb.risks_and_uncertainties = result.get("risks_and_uncertainties", [])
        fb.status = "COMPLETED"
        fb.completed_at = datetime.utcnow()
        db.commit()

        env = EventEnvelope.create(
            event_type=EVT_AI_FEEDBACK_GENERATED,
            producer="ms-006-ai-feedback",
            payload={"feedback_id": fb.id, "observation_id": observation_id,
                     "status": "AI_GENERATED_DRAFT"},
            correlation_id=observation_id,
            causation_id=transcription_id,
        )
        publish_event(r, STREAM_AI_FEEDBACK, env)
        logger.info("AI feedback generated for observation %s", observation_id)

    except Exception as exc:
        logger.error("AI feedback failed for observation %s: %s", observation_id, exc)
        try:
            fb.status = "FAILED"
            fb.error_message = str(exc)
            db.commit()
            env = EventEnvelope.create(
                event_type=EVT_AI_FEEDBACK_FAILED,
                producer="ms-006-ai-feedback",
                payload={"observation_id": observation_id, "error": str(exc)},
                correlation_id=observation_id,
            )
            publish_event(r, STREAM_AI_FEEDBACK, env)
        except Exception:
            pass
    finally:
        db.close()


def _run_consumer(redis_url: str) -> None:
    r = redis_lib.from_url(redis_url)
    logger.info("AI feedback consumer started.")
    while not _stop_event.is_set():
        try:
            messages = consume_events(r, STREAM_TRANSCRIPTION, CONSUMER_GROUP, CONSUMER_NAME,
                                      count=3, block_ms=2000)
            for msg_id, envelope in messages:
                if envelope.event_type == EVT_TRANSCRIPTION_COMPLETED:
                    _process_transcription_completed(envelope.payload, r)
                ack_event(r, STREAM_TRANSCRIPTION, CONSUMER_GROUP, msg_id)
        except Exception as exc:
            logger.warning("AI feedback consumer error: %s", exc)


def start_consumer(redis_url: str) -> threading.Thread:
    t = threading.Thread(target=_run_consumer, args=(redis_url,), daemon=True)
    t.start()
    return t
