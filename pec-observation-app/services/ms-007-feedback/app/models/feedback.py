from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from pec_shared.models_base import Base, gen_uuid


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, nullable=False, unique=True, index=True)
    strengths = Column(JSON, nullable=True)
    improvement_points = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    action_plan = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="DRAFT")
    version = Column(Integer, nullable=False, default=1)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeedbackVersion(Base):
    __tablename__ = "feedback_versions"

    id = Column(String, primary_key=True, default=gen_uuid)
    feedback_id = Column(String, nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=True)  # full feedback state
    edited_by = Column(String, nullable=True)
    edit_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String, primary_key=True, default=gen_uuid)
    feedback_id = Column(String, nullable=False, index=True)
    observation_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    owner = Column(String, nullable=True)  # Professor | PEC | Coordenação
    due_date = Column(String, nullable=True)
    expected_evidence = Column(Text, nullable=True)
    is_completed = Column(String, nullable=False, default="false")
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
