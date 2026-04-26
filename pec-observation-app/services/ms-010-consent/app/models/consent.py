from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text
from pec_shared.models_base import Base, gen_uuid


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, nullable=False, index=True)
    consent_type = Column(String, nullable=False)  # audio_recording | data_processing
    accepted_by_user_id = Column(String, nullable=False)
    accepted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    version = Column(String, nullable=False, default="v1.0")
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DeletionSchedule(Base):
    __tablename__ = "deletion_schedules"

    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, nullable=False, index=True)
    audio_minio_key = Column(String, nullable=False)
    scheduled_delete_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="SCHEDULED")  # SCHEDULED|COMPLETED|FAILED
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
