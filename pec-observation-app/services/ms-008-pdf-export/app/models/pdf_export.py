from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text
from pec_shared.models_base import Base, gen_uuid


class PDFExport(Base):
    __tablename__ = "pdf_exports"

    id = Column(String, primary_key=True, default=gen_uuid)
    observation_id = Column(String, nullable=False, index=True)
    feedback_id = Column(String, nullable=True)
    minio_key = Column(String, nullable=True)
    integrity_hash = Column(String, nullable=True)  # SHA-256 of PDF bytes
    status = Column(String, nullable=False, default="PENDING")
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
