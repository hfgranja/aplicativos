from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class CorpusCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CorpusCaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = "regression"
    journey: Optional[str] = None
    criticality: Optional[str] = "MEDIUM"
    input_payload: Optional[Any] = None
    expected_output: Optional[Any] = None


class CorpusCaseOut(BaseModel):
    id: str
    corpus_id: str
    title: str
    category: Optional[str]
    criticality: str
    last_status: Optional[str]
    fail_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CorpusOut(BaseModel):
    id: str
    application_id: str
    name: str
    total_cases: int
    created_at: datetime

    model_config = {"from_attributes": True}
