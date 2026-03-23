import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Integer
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class TestPlan(Base):
    __tablename__ = "test_plans"

    id = Column(String, primary_key=True, default=gen_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    engines = Column(JSON, default=list)  # list of engine names to run
    mode = Column(String, default="FULL")  # FAST | FULL | REGULATORY
    budget_seconds = Column(Integer, default=3600)
    config = Column(JSON, default=dict)
    version = Column(Integer, default=1)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Execution(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    test_plan_id = Column(String, ForeignKey("test_plans.id"))
    mode = Column(String, default="FULL")
    status = Column(String, default="PENDING")  # PENDING | RUNNING | COMPLETED | FAILED | CANCELLED
    triggered_by = Column(String, ForeignKey("users.id"))
    pipeline_ref = Column(String)
    commit_sha = Column(String)
    engines_run = Column(JSON, default=list)
    summary = Column(JSON, default=dict)
    pyramid_coverage = Column(JSON, default=dict)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="executions")
    findings = relationship("Finding", back_populates="execution", cascade="all, delete")
    test_runs = relationship("TestRun", back_populates="execution", cascade="all, delete")
    release_decision = relationship("ReleaseDecision", back_populates="execution", uselist=False)


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    engine = Column(String, nullable=False)
    pyramid_level = Column(Integer)
    status = Column(String, default="PENDING")
    score = Column(Integer)
    neural_insights = Column(JSON, default=list)
    summary = Column(Text)
    evidence = Column(JSON, default=dict)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="test_runs")
