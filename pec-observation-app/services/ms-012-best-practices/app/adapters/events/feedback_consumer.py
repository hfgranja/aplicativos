"""Consumes pec.feedback.events → extracts best-practice cards + queues video."""
import json
import logging
import threading

import httpx

from pec_shared.events import consume_events, ack_event, STREAM_FEEDBACK
from ...application.use_cases.extract_best_practices import extract_cards
from ...application.use_cases import video_queue
from ...database import SessionLocal
from ...models.practice import BestPracticeCardModel
from ...config import settings

logger = logging.getLogger(__name__)

CONSUMER_GROUP = "best-practices-service"
CONSUMER_NAME  = "best-practices-worker-1"
EVT_APPROVED   = "feedback.approved"
EVT_REVIEWED   = "feedback.human_reviewed"

_stop_event = threading.Event()


def _fetch_audio(observation_id: str) -> tuple[bytes | None, list[dict]]:
    audio_bytes = None
    segments: list[dict] = []
    try:
        r = httpx.get(f"{settings.AUDIO_SERVICE_URL}/api/v1/audio/{observation_id}/download",
                      timeout=15.0)
        if r.status_code == 200:
            audio_bytes = r.content
    except Exception as exc:
        logger.debug("Audio fetch failed %s: %s", observation_id, exc)
    try:
        r = httpx.get(
            f"{settings.TRANSCRIPTION_SERVICE_URL}/api/v1/transcriptions/{observation_id}/segments",
            timeout=10.0)
        if r.status_code == 200:
            segments = r.json().get("segments", [])
    except Exception as exc:
        logger.debug("Segments fetch failed %s: %s", observation_id, exc)
    return audio_bytes, segments


def _save_and_enqueue(cards, pec_id: str) -> None:
    db = SessionLocal()
    try:
        for card in cards:
            row = BestPracticeCardModel(
                id=card.id, title=card.title, criterion=card.criterion.value,
                subject=card.subject, grade=card.grade, excerpt=card.excerpt,
                ai_explanation=card.ai_explanation,
                audio_clip_key=card.audio_clip_key,
                rubric_alignment=json.dumps(card.rubric_alignment, ensure_ascii=False),
                tags=json.dumps(card.tags, ensure_ascii=False),
                status=card.status.value,
                source_observation_id=card.source_observation_id,
                created_by_pec_id=card.created_by_pec_id,
                created_at=card.created_at,
                video_status="pending",
            )
            db.add(row)
        db.commit()

        # Enqueue video generation for each saved card
        for card in cards:
            video_queue.enqueue(
                card_id       = card.id,
                card_data     = {
                    "title":          card.title,
                    "subject":        card.subject,
                    "grade":          card.grade,
                    "criterion":      card.criterion.value,
                    "excerpt":        card.excerpt,
                    "ai_explanation": card.ai_explanation,
                    "rubric_alignment": card.rubric_alignment,
                },
                audio_clip_key = card.audio_clip_key,
            )

        logger.info("Saved %d cards and enqueued video generation", len(cards))
    except Exception as exc:
        db.rollback()
        logger.error("Save/enqueue failed: %s", exc)
    finally:
        db.close()


def _process(payload: dict) -> None:
    observation_id = payload.get("observation_id", "")
    pec_id         = payload.get("pec_id", "system")
    subject        = payload.get("subject", "")
    grade          = payload.get("grade", "")
    feedback       = payload.get("feedback_data", {})

    if not feedback.get("strengths"):
        return

    audio_bytes, segments = _fetch_audio(observation_id)
    cards = extract_cards(
        observation_id=observation_id, pec_id=pec_id,
        subject=subject, grade=grade, feedback=feedback,
        audio_bytes=audio_bytes, segments=segments,
    )
    if cards:
        _save_and_enqueue(cards, pec_id)


def start_consumer(redis_client) -> None:
    def _loop():
        logger.info("Best-practices consumer started")
        while not _stop_event.is_set():
            try:
                msgs = consume_events(
                    redis_client, STREAM_FEEDBACK, CONSUMER_GROUP, CONSUMER_NAME
                )
                for msg_id, data in msgs:
                    if data.get("event_type") in (EVT_APPROVED, EVT_REVIEWED):
                        _process(json.loads(data.get("payload", "{}")))
                    ack_event(redis_client, STREAM_FEEDBACK, CONSUMER_GROUP, msg_id)
            except Exception as exc:
                logger.error("Consumer error: %s", exc)

    threading.Thread(target=_loop, daemon=True).start()


def stop_consumer() -> None:
    _stop_event.set()
