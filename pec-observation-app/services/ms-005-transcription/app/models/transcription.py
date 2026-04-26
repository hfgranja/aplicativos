from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from pec_shared.models_base import Base, gen_uuid


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, nullable=False, unique=True, index=True)
    audio_upload_id = Column(String, nullable=True)
    full_text = Column(Text, nullable=True)
    segments = Column(JSON, nullable=True)      # [{start, end, text, speaker}]
    language = Column(String, nullable=True, default="pt")
    duration_seconds = Column(Float, nullable=True)
    segment_count = Column(Integer, nullable=True)
    average_confidence = Column(Float, nullable=True)
    model_used = Column(String, nullable=True)
    status = Column(String, nullable=False, default="PENDING")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
