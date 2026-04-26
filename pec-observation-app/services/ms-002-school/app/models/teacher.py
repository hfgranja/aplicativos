from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, JSON, String
from pec_shared.models_base import Base, gen_uuid


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(String, primary_key=True, default=gen_uuid)
    school_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    registration_number = Column(String, nullable=True)  # RF number
    subjects = Column(JSON, default=list)
    grades = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
