"""Tracks URLs already crawled to avoid duplicate ingestion."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from pec_shared.models_base import Base


class CrawlLogModel(Base):
    __tablename__ = "crawl_log"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    url_hash   = Column(String(64), unique=True, nullable=False, index=True)
    url        = Column(Text, nullable=False)
    source     = Column(String(100), nullable=False)
    title      = Column(Text, nullable=True)
    doc_id     = Column(String(36), nullable=True)   # FK to knowledge_documents (soft ref)
    success    = Column(Boolean, default=True)
    error_msg  = Column(Text, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
