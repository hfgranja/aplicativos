from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReleaseDecisionOut(BaseModel):
    id: str
    execution_id: str
    decision: str
    score: Optional[int]
    blocking_findings: List[str]
    risk_acceptances: List[dict]
    pyramid_coverage_summary: dict
    decided_at: datetime
    notes: Optional[str]

    model_config = {"from_attributes": True}
