from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    policy_type: str
    application_id: Optional[str] = None
    rules: Optional[dict] = {}


class PolicyOut(BaseModel):
    id: str
    tenant_id: str
    application_id: Optional[str]
    name: str
    policy_type: str
    rules: dict
    is_active: bool
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}
