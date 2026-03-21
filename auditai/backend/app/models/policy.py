import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean, Integer
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    application_id = Column(String, ForeignKey("applications.id"))  # None = tenant-wide
    name = Column(String, nullable=False)
    description = Column(String)
    policy_type = Column(String)  # release | execution | data | retention | exception
    rules = Column(JSON, default=dict)
    # Example rules:
    # {
    #   "block_on_severity": ["CRITICAL", "HIGH"],
    #   "mutation_score_minimum": 70,
    #   "required_engines": ["sast", "contract"],
    #   "pyramid_levels_required": [1, 2, 5],
    #   "max_critical_findings": 0,
    # }
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
