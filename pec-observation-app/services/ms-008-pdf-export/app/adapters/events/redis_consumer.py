"""PDF Export service — consumes feedback.approved events."""
import hashlib
import logging
import threading
from datetime import datetime

import boto3
import redis as redis_lib
from botocore.config import Config

from pec_shared.events import (
    STREAM_FEEDBACK, STREAM_PDF,
    EVT_FEEDBACK_APPROVED, EVT_PDF_GENERATED, EVT_PDF_GENERATION_FAILED,
    EventEnvelope, consume_events, ack_event, publish_event,
)
from ...database import SessionLocal
from ...models.pdf_export import PDFExport
from ...config import settings

logger = logging.getLogger(__name__)
CONSUMER_GROUP = "pdf-export-service"
CONSUMER_NAME = "pdf-worker-1"

_stop_event = threading.Event()


def _upload_pdf(pdf_bytes: bytes, key: str) -> None:
    client = boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    import io
    client.upload_fileobj(io.BytesIO(pdf_bytes), settings.MINIO_BUCKET_PDF, key,
                          ExtraArgs={"ContentType": "application/pdf"})


def _process_feedback_approved(payload: dict, r) -> None:
    observation_id = payload.get("observation_id", "")
    feedback_id = payload.get("feedback_id", "")

    db = SessionLocal()
    try:
        existing = db.query(PDFExport).filter(
            PDFExport.observation_id == observation_id,
            PDFExport.status == "COMPLETED",
        ).first()
        if existing:
            return

        export = PDFExport(
            observation_id=observation_id,
            feedback_id=feedback_id,
            status="PROCESSING",
        )
        db.add(export)
        db.commit()
        db.refresh(export)

        from ...adapters.pdf.reportlab_adapter import generate_feedback_pdf, compute_hash
        pdf_bytes = generate_feedback_pdf(
            observation_id=observation_id,
            school_name=payload.get("school_name", ""),
            teacher_name=payload.get("teacher_name", ""),
            subject=payload.get("subject", ""),
            grade=payload.get("grade", ""),
            lesson_theme=payload.get("lesson_theme", ""),
            observed_at=payload.get("observed_at"),
            summary=payload.get("summary"),
            strengths=payload.get("strengths"),
            improvement_points=payload.get("improvement_points"),
            evidence=payload.get("evidence"),
            action_plan=payload.get("action_plan"),
        )
        pdf_hash = compute_hash(pdf_bytes)
        minio_key = f"pdf/{observation_id}/{export.id}.pdf"
        _upload_pdf(pdf_bytes, minio_key)

        export.minio_key = minio_key
        export.integrity_hash = pdf_hash
        export.status = "COMPLETED"
        export.generated_at = datetime.utcnow()
        db.commit()

        env = EventEnvelope.create(
            event_type=EVT_PDF_GENERATED,
            producer="ms-008-pdf-export",
            payload={"pdf_id": export.id, "observation_id": observation_id,
                     "minio_key": minio_key, "integrity_hash": pdf_hash},
            correlation_id=observation_id,
        )
        publish_event(r, STREAM_PDF, env)
        logger.info("PDF generated for observation %s", observation_id)

    except Exception as exc:
        logger.error("PDF generation failed for observation %s: %s", observation_id, exc)
        try:
            export.status = "FAILED"
            export.error_message = str(exc)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _run_consumer(redis_url: str) -> None:
    r = redis_lib.from_url(redis_url)
    logger.info("PDF export consumer started.")
    while not _stop_event.is_set():
        try:
            messages = consume_events(r, STREAM_FEEDBACK, CONSUMER_GROUP, CONSUMER_NAME,
                                      count=5, block_ms=2000)
            for msg_id, envelope in messages:
                if envelope.event_type == EVT_FEEDBACK_APPROVED:
                    _process_feedback_approved(envelope.payload, r)
                ack_event(r, STREAM_FEEDBACK, CONSUMER_GROUP, msg_id)
        except Exception as exc:
            logger.warning("PDF export consumer error: %s", exc)


def start_consumer(redis_url: str) -> threading.Thread:
    t = threading.Thread(target=_run_consumer, args=(redis_url,), daemon=True)
    t.start()
    return t
