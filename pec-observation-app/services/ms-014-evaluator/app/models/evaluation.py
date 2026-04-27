import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from pec_shared.models_base import Base


class FeedbackEvaluation(Base):
    """Evaluation record for one AI-generated → human-approved feedback pair."""
    __tablename__ = "feedback_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id = Column(String(128), nullable=False, unique=True, index=True)
    observation_id = Column(String(128), nullable=False, index=True)

    # Sub-scores (0.0 – 1.0 each)
    structural_score = Column(Float, nullable=False, default=0.0)
    evidence_score   = Column(Float, nullable=False, default=0.0)
    delta_score      = Column(Float, nullable=False, default=0.0)  # 1 - edit_ratio
    guardrail_score  = Column(Float, nullable=False, default=0.0)
    semantic_score   = Column(Float, nullable=False, default=0.0)  # embedding cos-sim

    # Composite quality score (weighted average of sub-scores)
    quality_score = Column(Float, nullable=False, default=0.0)

    # Combined weight used for Modelfile selection (quality × recency)
    selection_weight = Column(Float, nullable=False, default=0.0)

    details = Column(JSONB, default=dict)
    evaluated_at = Column(DateTime(timezone=True),
                          default=lambda: datetime.now(timezone.utc))


class ModelHealthSnapshot(Base):
    """Periodic snapshot of model health computed from recent evaluations."""
    __tablename__ = "model_health_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_at = Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc), index=True)
    window_size = Column(Integer, nullable=False)
    mean_quality = Column(Float, nullable=False)
    min_quality  = Column(Float, nullable=False)
    max_quality  = Column(Float, nullable=False)
    trend        = Column(Float, nullable=False)  # mean_quality - prev_window_mean
    status       = Column(String(32), nullable=False)
    # improving | stable | declining | degraded
    total_evaluated = Column(Integer, nullable=False, default=0)
    alert_triggered = Column(String(1), nullable=False, default="N")  # Y | N


class SyntheticExample(Base):
    """Synthetic training example generated to prevent model forgetting."""
    __tablename__ = "synthetic_examples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_feedback_id = Column(String(128), nullable=False, index=True)
    transcription_variant = Column(Text, nullable=False)
    feedback_variant = Column(Text, nullable=False)
    generation_method = Column(String(64), nullable=False, default="paraphrase")
    quality_score = Column(Float, nullable=False, default=0.5)
    is_active = Column(String(1), nullable=False, default="Y")
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
