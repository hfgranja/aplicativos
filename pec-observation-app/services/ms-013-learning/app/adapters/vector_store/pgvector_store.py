"""pgvector-backed store: upsert embeddings, cosine similarity search."""
import logging
import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.embedding import EmbeddingRecord

logger = logging.getLogger(__name__)


def upsert_embedding(
    db: Session,
    source_type: str,
    source_id: str,
    content: str,
    embedding: list[float],
    metadata: dict | None = None,
) -> EmbeddingRecord:
    existing = (
        db.query(EmbeddingRecord)
        .filter_by(source_type=source_type, source_id=source_id)
        .first()
    )
    if existing:
        existing.content = content
        existing.embedding = embedding
        existing.metadata_ = metadata or {}
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        return existing

    record = EmbeddingRecord(
        id=uuid.uuid4(),
        source_type=source_type,
        source_id=source_id,
        content=content,
        embedding=embedding,
        metadata_=metadata or {},
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def similarity_search(
    db: Session,
    query_embedding: list[float],
    source_types: list[str] | None = None,
    limit: int = 8,
) -> list[EmbeddingRecord]:
    """Return top-k records by cosine similarity to *query_embedding*."""
    # Build filter clause
    filter_clause = ""
    params: dict = {"limit": limit}

    if source_types:
        placeholders = ", ".join(f":st{i}" for i in range(len(source_types)))
        filter_clause = f"WHERE source_type IN ({placeholders})"
        for i, st in enumerate(source_types):
            params[f"st{i}"] = st

    # pgvector cosine distance operator <=>
    vec_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"
    sql = text(
        f"""
        SELECT id FROM embeddings
        {filter_clause}
        ORDER BY embedding <=> :vec
        LIMIT :limit
        """
    )
    params["vec"] = vec_literal
    rows = db.execute(sql, params).fetchall()
    ids = [r[0] for r in rows]
    if not ids:
        return []
    return db.query(EmbeddingRecord).filter(EmbeddingRecord.id.in_(ids)).all()


def count_by_type(db: Session, source_type: str) -> int:
    return db.query(EmbeddingRecord).filter_by(source_type=source_type).count()
