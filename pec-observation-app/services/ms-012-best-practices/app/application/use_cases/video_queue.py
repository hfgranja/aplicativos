"""In-process video generation queue.

A single background thread processes cards sequentially so video rendering
(CPU-bound) never blocks the FastAPI event loop.
"""
from __future__ import annotations

import logging
import queue
import threading
import uuid
from dataclasses import dataclass
from typing import Optional

from .generate_video import build_video
from .anonymize_content import anonymize_audio
from ...adapters.storage.minio_adapter import get_practice_clip
from ...database import SessionLocal
from ...models.practice import BestPracticeCardModel

logger = logging.getLogger(__name__)


@dataclass
class VideoJob:
    card_id:       str
    card_data:     dict
    audio_clip_key: Optional[str]


_q: queue.Queue[VideoJob] = queue.Queue()
_stop = threading.Event()


def enqueue(card_id: str, card_data: dict, audio_clip_key: Optional[str]) -> None:
    _q.put(VideoJob(card_id=card_id, card_data=card_data,
                    audio_clip_key=audio_clip_key))
    logger.info("Video job enqueued for card %s", card_id)


def _set_status(card_id: str, status: str,
                video_key: Optional[str] = None,
                duration: Optional[int] = None) -> None:
    db = SessionLocal()
    try:
        card = db.query(BestPracticeCardModel).filter(
            BestPracticeCardModel.id == card_id
        ).first()
        if card:
            card.video_status = status
            if video_key is not None:
                card.video_key = video_key
            if duration is not None:
                card.video_duration_s = duration
            db.commit()
    except Exception as exc:
        logger.error("DB update failed for card %s: %s", card_id, exc)
        db.rollback()
    finally:
        db.close()


def _worker() -> None:
    logger.info("Video generation worker started")
    while not _stop.is_set():
        try:
            job = _q.get(timeout=2)
        except queue.Empty:
            continue

        logger.info("Processing video for card %s", job.card_id)
        _set_status(job.card_id, "processing")

        # Fetch and re-anonymise audio if available
        audio_bytes: Optional[bytes] = None
        if job.audio_clip_key:
            raw = get_practice_clip(job.audio_clip_key)
            if raw:
                audio_bytes = anonymize_audio(raw)

        video_key = f"best-practices/videos/{job.card_id}.mp4"
        try:
            key, duration = build_video(job.card_data, audio_bytes, video_key)
            _set_status(job.card_id, "ready", key, duration)
            logger.info("Video ready for card %s (%d s)", job.card_id, duration)
        except Exception as exc:
            logger.error("Video generation failed for card %s: %s", job.card_id, exc)
            _set_status(job.card_id, "failed")

        _q.task_done()


def start() -> None:
    t = threading.Thread(target=_worker, daemon=True, name="video-worker")
    t.start()


def stop() -> None:
    _stop.set()
