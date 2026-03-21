from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ExecutionCreate(BaseModel):
    application_id: str
    mode: Optional[str] = "FULL"
    engines: Optional[List[str]] = None  # None = use default for mode
    pipeline_ref: Optional[str] = None
    commit_sha: Optional[str] = None


class ExecutionOut(BaseModel):
    id: str
    tenant_id: str
    application_id: str
    mode: str
    status: str
    engines_run: Optional[List[str]]
    summary: Optional[dict]
    pyramid_coverage: Optional[dict]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class TestRunOut(BaseModel):
    id: str
    execution_id: str
    engine: str
    pyramid_level: Optional[int]
    status: str
    score: Optional[int]
    neural_insights: Optional[List[str]]
    summary: Optional[str]
    execution_time_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
