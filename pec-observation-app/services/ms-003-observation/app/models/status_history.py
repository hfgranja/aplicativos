from datetime import datetime
from sqlalchemy import Column, DateTime, String
from pec_shared.models_base import Base, gen_uuid


class StatusHistory(Base):
    __tablename__ = "observation_status_history"

    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, nullable=False, index=True)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    transitioned_by = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    transitioned_at = Column(DateTime, default=datetime.utcnow)
