from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String
from pec_shared.models_base import Base, gen_uuid


class School(Base):
    __tablename__ = "schools"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    district = Column(String, nullable=False)
    external_reference = Column(String, nullable=True)  # INEP code
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
