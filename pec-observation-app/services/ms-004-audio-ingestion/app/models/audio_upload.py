from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from pec_shared.models_base import Base, gen_uuid


class AudioUpload(Base):
    __tablename__ = "audio_uploads"

    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, nullable=False, index=True)
    minio_key = Column(String, nullable=True)
    status = Column(String, nullable=False, default="PENDING")  # PENDING|CONFIRMED|FAILED
    file_size_bytes = Column(Integer, nullable=True)
    checksum = Column(String, nullable=True)
    codec = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    idempotency_key = Column(String, nullable=True, unique=True)
    upload_url_expires_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
