from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, String
from pec_shared.models_base import Base, gen_uuid


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    event_id = Column(String, nullable=False, unique=True)
    event_type = Column(String, nullable=False, index=True)
    event_version = Column(String, nullable=True)
    occurred_at = Column(String, nullable=True)
    correlation_id = Column(String, nullable=True, index=True)
    causation_id = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True)
    producer = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    stream = Column(String, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
