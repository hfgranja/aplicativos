import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    criticality = Column(String, default="MEDIUM")  # LOW | MEDIUM | HIGH | CRITICAL
    domain = Column(String)
    data_types = Column(JSON, default=list)
    has_ai_code = Column(Boolean, default=False)
    stack_info = Column(JSON, default=dict)
    squad = Column(String)
    owner_id = Column(String, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repositories = relationship("Repository", back_populates="application", cascade="all, delete")
    contracts = relationship("Contract", back_populates="application", cascade="all, delete")
    executions = relationship("Execution", back_populates="application")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=gen_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    url = Column(String)
    branch = Column(String, default="main")
    provider = Column(String)  # github | gitlab | bitbucket
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="repositories")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=gen_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    name = Column(String, nullable=False)
    contract_type = Column(String)  # openapi | asyncapi | graphql | protobuf
    version = Column(String)
    content = Column(Text)
    file_path = Column(String)
    is_baseline = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="contracts")
