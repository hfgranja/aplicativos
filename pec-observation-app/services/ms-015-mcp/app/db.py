"""Database models and session factories for the MCP server.

Mirrors the tables defined in ms-013-learning and ms-014-evaluator without
importing from those services — the MCP server is read-only and standalone.
"""
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (Column, DateTime, Float, Integer, String, Text,
                        create_engine)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


# ── Learning DB models ────────────────────────────────────────────────────────

class EmbeddingRecord(Base):
    __tablename__ = "embeddings"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type    = Column(String(64),  nullable=False, index=True)
    source_id      = Column(String(128), nullable=False, index=True)
    content        = Column(Text, nullable=False)
    embedding      = Column(Vector(768), nullable=True)
    metadata_      = Column("metadata", JSONB, default=dict)
    quality_score  = Column(Float, nullable=True)
    selection_weight = Column(Float, nullable=True)
    created_at     = Column(DateTime(timezone=True),
                            default=lambda: datetime.now(timezone.utc))
    updated_at     = Column(DateTime(timezone=True),
                            default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))


class ModelBuild(Base):
    __tablename__ = "model_builds"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name     = Column(String(128), nullable=False)
    base_model     = Column(String(128), nullable=False)
    examples_count = Column(String(16),  nullable=False)
    status         = Column(String(32),  nullable=False, default="pending")
    error          = Column(Text, nullable=True)
    built_at       = Column(DateTime(timezone=True), nullable=True)
    created_at     = Column(DateTime(timezone=True),
                            default=lambda: datetime.now(timezone.utc))


# ── Evaluator DB models ───────────────────────────────────────────────────────

class FeedbackEvaluation(Base):
    __tablename__ = "feedback_evaluations"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id      = Column(String(128), nullable=False, index=True)
    observation_id   = Column(String(128), nullable=True)
    quality_score    = Column(Float, nullable=False)
    structural_score = Column(Float, nullable=True)
    evidence_score   = Column(Float, nullable=True)
    delta_score      = Column(Float, nullable=True)
    guardrail_score  = Column(Float, nullable=True)
    semantic_score   = Column(Float, nullable=True)
    details          = Column(JSONB, default=dict)
    created_at       = Column(DateTime(timezone=True),
                              default=lambda: datetime.now(timezone.utc))


class HealthSnapshot(Base):
    __tablename__ = "health_snapshots"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mean_quality = Column(Float, nullable=False)
    trend        = Column(Float, nullable=False)
    status       = Column(String(32), nullable=False)
    sample_count = Column(Integer, nullable=False)
    details      = Column(JSONB, default=dict)
    created_at   = Column(DateTime(timezone=True),
                          default=lambda: datetime.now(timezone.utc))


# ── Session factories ─────────────────────────────────────────────────────────

_engine_learning  = create_engine(settings.database_url,
                                   pool_pre_ping=True, pool_size=3)
_engine_evaluator = create_engine(settings.database_url_evaluator,
                                   pool_pre_ping=True, pool_size=3)

_SessionLearning  = sessionmaker(bind=_engine_learning,  autoflush=False)
_SessionEvaluator = sessionmaker(bind=_engine_evaluator, autoflush=False)


@contextmanager
def learning_db():
    db = _SessionLearning()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def evaluator_db():
    db = _SessionEvaluator()
    try:
        yield db
    finally:
        db.close()
