"""Ingest approved human feedback as a learning example."""
import json
import logging

from sqlalchemy.orm import Session

from app.adapters.embedding.ollama_embedding import embed
from app.adapters.vector_store.pgvector_store import count_by_type, upsert_embedding
from app.config import settings

logger = logging.getLogger(__name__)


def ingest_approved_feedback(
    db: Session,
    feedback_id: str,
    transcription_snippet: str,
    feedback_dict: dict,
    observation_context: dict | None = None,
) -> int:
    """Store an approved feedback as a few-shot example.

    Returns total count of approved examples stored so far.
    """
    if not transcription_snippet.strip():
        return count_by_type(db, "approved_feedback")

    # Embed the transcription so future queries can find similar examples
    snippet = transcription_snippet[:4000]
    try:
        vector = embed(snippet, settings.ollama_base_url, settings.ollama_embedding_model)
    except Exception as exc:
        logger.warning("Could not embed feedback %s: %s", feedback_id, exc)
        return count_by_type(db, "approved_feedback")

    upsert_embedding(
        db=db,
        source_type="approved_feedback",
        source_id=feedback_id,
        content=snippet,
        embedding=vector,
        metadata={
            "transcription_snippet": snippet,
            "feedback_json": json.dumps(feedback_dict, ensure_ascii=False),
            "context": observation_context or {},
        },
    )
    total = count_by_type(db, "approved_feedback")
    logger.info("Ingested approved feedback %s (total=%d)", feedback_id, total)
    return total
