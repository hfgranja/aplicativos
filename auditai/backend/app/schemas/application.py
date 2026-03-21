from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ApplicationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    criticality: Optional[str] = "MEDIUM"
    domain: Optional[str] = None
    data_types: Optional[List[str]] = []
    has_ai_code: Optional[bool] = False
    squad: Optional[str] = None
    owner_id: Optional[str] = None


class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    criticality: Optional[str] = None
    domain: Optional[str] = None
    data_types: Optional[List[str]] = None
    has_ai_code: Optional[bool] = None
    squad: Optional[str] = None
    stack_info: Optional[dict] = None


class ApplicationOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    criticality: str
    domain: Optional[str]
    data_types: Optional[List[str]]
    has_ai_code: bool
    stack_info: Optional[dict]
    squad: Optional[str]
    owner_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractCreate(BaseModel):
    name: str
    contract_type: str  # openapi | asyncapi | graphql | protobuf
    version: Optional[str] = None
    content: Optional[str] = None
    is_baseline: Optional[bool] = False


class ContractOut(BaseModel):
    id: str
    application_id: str
    name: str
    contract_type: str
    version: Optional[str]
    is_baseline: bool
    created_at: datetime

    model_config = {"from_attributes": True}
