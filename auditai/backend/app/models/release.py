import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class ReleaseDecision(Base):
    __tablename__ = "release_decisions"

    id = Column(String, primary_key=True, default=gen_uuid)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False, unique=True)
    decision = Column(String, nullable=False)  # GREEN | YELLOW | RED
    score = Column(Integer)
    blocking_findings = Column(JSON, default=list)
    risk_acceptances = Column(JSON, default=list)
    pyramid_coverage_summary = Column(JSON, default=dict)
    policy_id = Column(String, ForeignKey("policies.id"))
    decided_by = Column(String, ForeignKey("users.id"))
    decided_at = Column(DateTime, default=datetime.utcnow)
    pipeline_ref = Column(String)
    notes = Column(String)

    execution = relationship("Execution", back_populates="release_decision")
