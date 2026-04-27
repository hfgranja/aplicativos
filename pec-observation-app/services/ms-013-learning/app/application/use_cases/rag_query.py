"""RAG context retrieval — called by MS-006 before generating feedback."""
import logging

from sqlalchemy.orm import Session

from app.adapters.embedding.ollama_embedding import embed
from app.adapters.vector_store.pgvector_store import similarity_search
from app.config import settings

logger = logging.getLogger(__name__)


def retrieve_context(
    db: Session,
    query_text: str,
    source_types: list[str] | None = None,
    limit: int = 6,
) -> list[dict]:
    """Return top-k relevant chunks for *query_text*.

    *source_types* filters by record type; defaults to knowledge docs + approved feedback.
    """
    if source_types is None:
        source_types = ["knowledge_document", "approved_feedback", "best_practice"]

    try:
        query_vec = embed(query_text, settings.ollama_base_url, settings.ollama_embedding_model)
    except Exception as exc:
        logger.warning("Embedding query failed, returning empty context: %s", exc)
        return []

    records = similarity_search(db, query_vec, source_types=source_types, limit=limit)

    results = []
    for rec in records:
        results.append({
            "source_type": rec.source_type,
            "source_id": rec.source_id,
            "content": rec.content,
            "metadata": rec.metadata_ or {},
        })
    return results
