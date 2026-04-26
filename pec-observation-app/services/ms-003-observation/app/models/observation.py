from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from pec_shared.models_base import Base, gen_uuid


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String, primary_key=True, default=gen_uuid)
    school_id = Column(String, nullable=False, index=True)
    teacher_id = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    grade = Column(String, nullable=False)
    lesson_theme = Column(String, nullable=False)
    lesson_objectives = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="DRAFT")
    audio_local_path = Column(String, nullable=True)
    audio_minio_key = Column(String, nullable=True)
    audio_duration_seconds = Column(Integer, nullable=True)
    audio_checksum = Column(String, nullable=True)
    audio_codec = Column(String, nullable=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
