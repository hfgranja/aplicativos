import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Float, Boolean, Integer
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=gen_uuid)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    test_run_id = Column(String, ForeignKey("test_runs.id"))
    engine = Column(String, nullable=False)
    pyramid_level = Column(Integer)
    severity = Column(String, nullable=False)  # INFO | LOW | MEDIUM | HIGH | CRITICAL
    category = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    evidence = Column(JSON, default=dict)
    seed = Column(Text)
    file_path = Column(String)
    line_number = Column(Integer)
    cwe_id = Column(String)
    neural_score = Column(Float)
    fix_proposal = Column(JSON)  # FixProposal schema
    is_accepted_risk = Column(Boolean, default=False)
    accepted_by = Column(String, ForeignKey("users.id"))
    accepted_at = Column(DateTime)
    acceptance_justification = Column(Text)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="findings")
    evidences = relationship("Evidence", back_populates="finding", cascade="all, delete")


class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(String, primary_key=True, default=gen_uuid)
    finding_id = Column(String, ForeignKey("findings.id"), nullable=False)
    evidence_type = Column(String)  # input | output | trace | diff | screenshot
    content = Column(Text)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    finding = relationship("Finding", back_populates="evidences")
