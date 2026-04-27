from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from pec_shared.models_base import Base


class KnowledgeDocumentModel(Base):
    __tablename__ = "knowledge_documents"

    id              = Column(String, primary_key=True)
    title           = Column(String(500), nullable=False)
    document_type   = Column(String(50), nullable=False)
    source_filename = Column(String(500), nullable=False)
    description     = Column(Text, nullable=True)
    full_text       = Column(Text, nullable=False)
    chunk_count     = Column(Integer, default=0)
    uploaded_by     = Column(String, nullable=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text        = Column(Text, nullable=False)
    char_start  = Column(Integer, nullable=False)
    char_end    = Column(Integer, nullable=False)
