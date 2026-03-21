import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(String, primary_key=True, default=gen_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    version = Column(String)
    commit_sha = Column(String)
    artifact_path = Column(String)
    is_active = Column(Boolean, default=True)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Corpus(Base):
    __tablename__ = "corpora"

    id = Column(String, primary_key=True, default=gen_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    total_cases = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cases = relationship("CorpusCase", back_populates="corpus", cascade="all, delete")


class CorpusCase(Base):
    __tablename__ = "corpus_cases"

    id = Column(String, primary_key=True, default=gen_uuid)
    corpus_id = Column(String, ForeignKey("corpora.id"), nullable=False)
    title = Column(String)
    description = Column(Text)
    category = Column(String)  # bug | edge_case | security | regression
    journey = Column(String)
    criticality = Column(String, default="MEDIUM")
    input_payload = Column(JSON)
    expected_output = Column(JSON)
    is_anonymized = Column(Boolean, default=False)
    source_finding_id = Column(String, ForeignKey("findings.id"))
    last_executed_at = Column(DateTime)
    last_status = Column(String)
    fail_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    corpus = relationship("Corpus", back_populates="cases")
