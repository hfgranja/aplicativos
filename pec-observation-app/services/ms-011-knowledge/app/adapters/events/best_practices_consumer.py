"""MS-011 auto-learning consumer.

Listens to pec.feedback.events for feedback.human_reviewed events.
Extracts approved strengths and ingests them as feedback_example knowledge
chunks so future RAG calls benefit from accumulated real-world best practices.
"""
import json
import logging
import threading
import uuid

from pec_shared.events import consume_events, ack_event, STREAM_FEEDBACK
from ..application.use_cases.ingest_document import IngestDocumentUseCase, IngestInput
from ...database import SessionLocal

logger = logging.getLogger(__name__)

CONSUMER_GROUP = "knowledge-autolearn"
CONSUMER_NAME  = "knowledge-autolearn-worker-1"
EVT_REVIEWED   = "feedback.human_reviewed"
EVT_APPROVED   = "feedback.approved"

_stop_event = threading.Event()


def _build_practice_text(strengths: list[dict], subject: str, grade: str) -> str:
    """Compose a readable best-practice chunk from structured strength items."""
    lines = [
        f"Componente: {subject}  |  Turma: {grade}",
        "Pontos fortes identificados na observação:",
    ]
    for s in strengths:
        title = s.get("title", "")
        desc  = s.get("description", "")
        ev    = s.get("evidence", "")
        lines.append(f"\n• {title}: {desc}")
        if ev:
            lines.append(f'  Evidência: "{ev}"')
    return "\n".join(lines)


def _process_feedback_reviewed(payload: dict) -> None:
    feedback_data = payload.get("feedback_data", {})
    strengths = feedback_data.get("strengths", [])
    if not strengths:
        return

    subject = payload.get("subject", "")
    grade   = payload.get("grade", "")
    obs_id  = payload.get("observation_id", str(uuid.uuid4()))

    text = _build_practice_text(strengths, subject, grade)
    uc   = IngestDocumentUseCase()
    inp  = IngestInput(
        file_bytes=text.encode("utf-8"),
        filename=f"autolearn_{obs_id}.txt",
        title=f"Boas práticas — {subject} {grade} (obs {obs_id[:8]})",
        document_type="feedback_example",
        description="Gerado automaticamente a partir de feedback humano aprovado.",
        uploaded_by="system-autolearn",
    )
    db = SessionLocal()
    try:
        doc = uc.execute(inp, db)
        logger.info("Auto-learned %d chunks from observation %s", doc.chunk_count, obs_id)
    except Exception as exc:
        logger.error("Auto-learn failed for obs %s: %s", obs_id, exc)
    finally:
        db.close()


def start_consumer(redis_client) -> None:
    def _loop():
        logger.info("Knowledge auto-learn consumer started")
        while not _stop_event.is_set():
            try:
                msgs = consume_events(
                    redis_client, STREAM_FEEDBACK, CONSUMER_GROUP, CONSUMER_NAME
                )
                for msg_id, data in msgs:
                    event_type = data.get("event_type", "")
                    if event_type in (EVT_REVIEWED, EVT_APPROVED):
                        payload = json.loads(data.get("payload", "{}"))
                        _process_feedback_reviewed(payload)
                    ack_event(redis_client, STREAM_FEEDBACK, CONSUMER_GROUP, msg_id)
            except Exception as exc:
                logger.error("Auto-learn consumer error: %s", exc)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


def stop_consumer():
    _stop_event.set()
