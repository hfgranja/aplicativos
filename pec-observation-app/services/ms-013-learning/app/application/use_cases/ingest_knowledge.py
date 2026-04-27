"""Ingest a knowledge document (crawled page, official doc) into the vector store."""
import logging

from sqlalchemy.orm import Session

from app.adapters.embedding.ollama_embedding import embed
from app.adapters.vector_store.pgvector_store import upsert_embedding
from app.config import settings

logger = logging.getLogger(__name__)


def ingest_knowledge_document(
    db: Session,
    doc_id: str,
    title: str,
    content: str,
    source_url: str = "",
    extra_meta: dict | None = None,
) -> None:
    if not content.strip():
        return
    # Truncate to ~8000 chars to keep embeddings fast and focused
    snippet = content[:8000]
    try:
        vector = embed(snippet, settings.ollama_base_url, settings.ollama_embedding_model)
    except Exception as exc:
        logger.warning("Could not embed knowledge doc %s: %s", doc_id, exc)
        return

    upsert_embedding(
        db=db,
        source_type="knowledge_document",
        source_id=doc_id,
        content=snippet,
        embedding=vector,
        metadata={
            "title": title,
            "source_url": source_url,
            **(extra_meta or {}),
        },
    )
    logger.info("Ingested knowledge doc %s (%d chars)", doc_id, len(snippet))


def ingest_crawl_page(
    db: Session,
    url: str,
    title: str,
    text: str,
) -> None:
    doc_id = f"crawl:{url}"
    ingest_knowledge_document(
        db=db,
        doc_id=doc_id,
        title=title,
        content=text,
        source_url=url,
        extra_meta={"type": "crawl"},
    )
