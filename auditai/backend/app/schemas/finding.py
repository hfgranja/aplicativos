from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class FixProposal(BaseModel):
    explanation: str
    before_code: str
    after_code: str
    diff: str
    rationale: str
    confidence: float
    generated_by: str
    generated_at: datetime


class FindingOut(BaseModel):
    id: str
    execution_id: str
    engine: str
    pyramid_level: Optional[int]
    severity: str
    category: Optional[str]
    title: str
    description: Optional[str]
    evidence: Optional[dict]
    seed: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    cwe_id: Optional[str]
    neural_score: Optional[float]
    fix_proposal: Optional[dict]
    is_accepted_risk: bool
    accepted_by: Optional[str]
    accepted_at: Optional[datetime]
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class AcceptRiskRequest(BaseModel):
    justification: str


class FindingsFilter(BaseModel):
    severity: Optional[str] = None
    engine: Optional[str] = None
    is_resolved: Optional[bool] = None
    execution_id: Optional[str] = None
