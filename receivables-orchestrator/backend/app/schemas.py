from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- Merchant / Policy ----------

class MerchantOut(BaseModel):
    id: str
    name: str
    document: Optional[str] = None
    segment: Optional[str] = None
    api_key: str

    class Config:
        from_attributes = True


class PolicyWeights(BaseModel):
    conversion: float = 0.22
    cost: float = 0.22
    risk: float = 0.22
    liquidity: float = 0.14
    experience: float = 0.12
    preference: float = 0.08


class MerchantPolicyIn(BaseModel):
    name: str
    objective: str = "balanced"
    weights: PolicyWeights = Field(default_factory=PolicyWeights)
    max_exposure: float = 50000.0
    allowed_methods: list[str] = ["pix", "credit_card", "boleto"]
    operation_mode: str = "recommendation"
    confidence_threshold: float = 0.55
    is_default: bool = False


class MerchantPolicyOut(MerchantPolicyIn):
    id: str
    merchant_id: str

    class Config:
        from_attributes = True


# ---------- Customer ----------

class CustomerOut(BaseModel):
    id: str
    name: str
    document: Optional[str] = None
    segment: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Intent ----------

class ReceivableIntentIn(BaseModel):
    merchant_id: str
    customer_id: str
    amount: float
    currency: str = "BRL"
    due_date: datetime
    objective: str = "balanced"
    allowed_payment_methods: list[str] = []
    forbidden_payment_methods: list[str] = []
    max_cost: Optional[float] = None  # percentage, e.g. 3.5
    max_risk: str = "medium"
    liquidity_need: str = "standard"
    customer_context: dict[str, Any] = {}
    merchant_policy: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    idempotency_key: Optional[str] = None


class ReceivableIntentOut(BaseModel):
    id: str
    merchant_id: str
    customer_id: str
    amount: float
    currency: str
    due_date: datetime
    objective: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OptionScoreOut(BaseModel):
    method: str
    provider_name: Optional[str] = None
    eligible: bool
    exclusion_reason: Optional[str] = None
    estimated_cost_pct: float
    estimated_conversion: float
    estimated_settlement_hours: float
    estimated_risk: float
    estimated_experience: float
    preference_match: float
    score: Optional[float] = None
    confidence: Optional[float] = None
    rank: Optional[int] = None


class RecommendationOut(BaseModel):
    intent_id: str
    status: str
    model_version: str
    recommended_method: Optional[str] = None
    operation_mode: str
    options: list[OptionScoreOut]

    model_config = {"protected_namespaces": ()}


class ExecuteIn(BaseModel):
    approved_route: str  # payment method chosen (may equal recommended)
    approved_by: str = "user_demo"


class ExplanationAudienceOut(BaseModel):
    audience: str
    text: str


class ExplanationOut(BaseModel):
    intent_id: str
    chosen_method: Optional[str]
    reason_summary: str
    discarded_options: list[dict[str, Any]]
    weights_applied: dict[str, float]
    audiences: list[ExplanationAudienceOut]


class AttemptOut(BaseModel):
    id: str
    method: str
    status: str
    attempt_number: int
    provider_ref: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    class Config:
        from_attributes = True


class RouteOut(BaseModel):
    id: str
    chosen_method: str
    status: str
    mode: str
    hop_index: int
    triggered_by: str
    created_at: datetime
    attempts: list[AttemptOut] = []

    class Config:
        from_attributes = True


class IntentTimelineOut(BaseModel):
    intent: ReceivableIntentOut
    routes: list[RouteOut]


class WebhookIn(BaseModel):
    provider_event_id: str
    route_id: str
    status: str  # confirmed|failed
    amount: Optional[float] = None
    failure_reason: Optional[str] = None


class SettlementOut(BaseModel):
    id: str
    attempt_id: str
    gross_amount: float
    fee: float
    net_amount: float
    expected_settlement_at: Optional[datetime]
    settled_at: Optional[datetime]
    reconciled: bool = False
    discrepancy_amount: float = 0.0

    class Config:
        from_attributes = True


class MetricsOut(BaseModel):
    merchant_id: str
    period_days: int
    total_intents: int
    conversion_rate: float
    avg_cost_pct: float
    avg_time_to_payment_hours: float
    fallback_rate: float
    retry_success_rate: float
    chargeback_rate_proxy: float
    conversion_by_method: dict[str, float]
    cost_by_method: dict[str, float]
    volume_by_method: dict[str, float]


class AuditLogOut(BaseModel):
    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    before: Optional[dict[str, Any]]
    after: Optional[dict[str, Any]]
    timestamp: datetime
    prev_hash: Optional[str]
    hash: str

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: str
    severity: str
    category: str
    message: str
    context: dict[str, Any]
    acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True
