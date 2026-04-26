"""Transcription service — consumes audio.uploaded events from pec.audio.events."""
import logging
import os
import tempfile
import threading

import boto3
import redis as redis_lib
from botocore.config import Config

from pec_shared.events import (
    STREAM_AUDIO, STREAM_TRANSCRIPTION,
    EVT_AUDIO_UPLOADED, EVT_TRANSCRIPTION_STARTED,
    EVT_TRANSCRIPTION_COMPLETED, EVT_TRANSCRIPTION_FAILED,
    EventEnvelope, consume_events, ack_event, publish_event,
)
from ...database import SessionLocal
from ...models.transcription import Transcription
from ...config import settings

logger = logging.getLogger(__name__)
CONSUMER_GROUP = "transcription-service"
CONSUMER_NAME = "transcription-worker-1"

_stop_event = threading.Event()


def _download_from_minio(minio_key: str, local_path: str) -> None:
    client = boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    client.download_file(settings.MINIO_BUCKET_AUDIO, minio_key, local_path)


def _process_audio_uploaded(payload: dict, r) -> None:
    observation_id = payload.get("observation_id", "")
    minio_key = payload.get("minio_key", "")
    upload_id = payload.get("upload_id", "")

    db = SessionLocal()
    try:
        existing = db.query(Transcription).filter(
            Transcription.observation_id == observation_id
        ).first()
        if existing and existing.status == "COMPLETED":
            return

        if not existing:
            transcript = Transcription(
                observation_id=observation_id,
                audio_upload_id=upload_id,
                status="PROCESSING",
            )
            db.add(transcript)
            db.commit()
            db.refresh(transcript)
        else:
            transcript = existing
            transcript.status = "PROCESSING"
            db.commit()

        env = EventEnvelope.create(
            event_type=EVT_TRANSCRIPTION_STARTED,
            producer="ms-005-transcription",
            payload={"transcription_id": transcript.id, "observation_id": observation_id},
            correlation_id=observation_id, causation_id=upload_id,
        )
        publish_event(r, STREAM_TRANSCRIPTION, env)

        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            _download_from_minio(minio_key, tmp_path)
            from ...adapters.transcription.whisper_adapter import transcribe
            result = transcribe(
                tmp_path,
                model_size=settings.WHISPER_MODEL_SIZE,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
            )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        transcript.full_text = result.text
        transcript.segments = [
            {"start": s.start, "end": s.end, "text": s.text, "speaker": s.speaker}
            for s in result.segments
        ]
        transcript.language = result.language
        transcript.duration_seconds = result.duration_seconds
        transcript.segment_count = len(result.segments)
        transcript.model_used = result.model_used
        transcript.status = "COMPLETED"
        from datetime import datetime
        transcript.completed_at = datetime.utcnow()
        db.commit()

        env = EventEnvelope.create(
            event_type=EVT_TRANSCRIPTION_COMPLETED,
            producer="ms-005-transcription",
            payload={
                "transcription_id": transcript.id,
                "observation_id": observation_id,
                "language": result.language,
                "segment_count": len(result.segments),
                "duration_seconds": result.duration_seconds,
            },
            correlation_id=observation_id,
            causation_id=upload_id,
        )
        publish_event(r, STREAM_TRANSCRIPTION, env)
        logger.info("Transcription completed for observation %s", observation_id)

    except Exception as exc:
        logger.error("Transcription failed for observation %s: %s", observation_id, exc)
        try:
            transcript.status = "FAILED"
            transcript.error_message = str(exc)
            db.commit()
            env = EventEnvelope.create(
                event_type=EVT_TRANSCRIPTION_FAILED,
                producer="ms-005-transcription",
                payload={"observation_id": observation_id, "error": str(exc)},
                correlation_id=observation_id,
            )
            publish_event(r, STREAM_TRANSCRIPTION, env)
        except Exception:
            pass
    finally:
        db.close()


def _run_consumer(redis_url: str) -> None:
    r = redis_lib.from_url(redis_url)
    logger.info("Transcription consumer started.")
    while not _stop_event.is_set():
        try:
            messages = consume_events(r, STREAM_AUDIO, CONSUMER_GROUP, CONSUMER_NAME,
                                      count=5, block_ms=2000)
            for msg_id, envelope in messages:
                if envelope.event_type == EVT_AUDIO_UPLOADED:
                    _process_audio_uploaded(envelope.payload, r)
                ack_event(r, STREAM_AUDIO, CONSUMER_GROUP, msg_id)
        except Exception as exc:
            logger.warning("Transcription consumer error: %s", exc)


def start_consumer(redis_url: str) -> threading.Thread:
    t = threading.Thread(target=_run_consumer, args=(redis_url,), daemon=True)
    t.start()
    return t
