from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, String, Text
from pec_shared.models_base import Base, gen_uuid


class AIFeedback(Base):
    __tablename__ = "ai_feedbacks"

    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, nullable=False, unique=True, index=True)
    transcription_id = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    improvement_points = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    suggested_action_plan = Column(JSON, nullable=True)
    risks_and_uncertainties = Column(JSON, nullable=True)
    model_provider = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True, default="v1.0")
    status = Column(String, nullable=False, default="PENDING")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
