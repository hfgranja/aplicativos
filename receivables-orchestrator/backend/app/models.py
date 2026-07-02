import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=lambda: gen_id("mch"))
    name = Column(String, nullable=False)
    document = Column(String)
    segment = Column(String)
    api_key = Column(String, unique=True, index=True, default=lambda: uuid.uuid4().hex)
    created_at = Column(DateTime, default=datetime.utcnow)

    policies = relationship("MerchantPolicy", back_populates="merchant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
    intents = relationship("ReceivableIntent", back_populates="merchant", cascade="all, delete-orphan")


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"

    id = Column(String, primary_key=True, default=lambda: gen_id("pol"))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    name = Column(String, nullable=False)
    objective = Column(String, default="balanced")  # maximize_conversion|minimize_cost|minimize_risk|maximize_liquidity|maximize_experience|balanced
    weights = Column(JSON, default=dict)  # {conversion, cost, risk, liquidity, experience, preference}
    max_exposure = Column(Float, default=50000.0)
    allowed_methods = Column(JSON, default=lambda: ["pix", "credit_card", "boleto"])
    operation_mode = Column(String, default="recommendation")  # recommendation|assisted|automatic|conservative
    confidence_threshold = Column(Float, default=0.55)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    merchant = relationship("Merchant", back_populates="policies")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: gen_id("cus"))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    name = Column(String, nullable=False)
    document = Column(String)
    segment = Column(String, default="b2c")  # b2c|b2b_recurring|b2b_avulso
    contact_phone = Column(String)
    contact_email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    merchant = relationship("Merchant", back_populates="customers")
    preference = relationship("CustomerPreference", back_populates="customer", uselist=False, cascade="all, delete-orphan")


class CustomerPreference(Base):
    __tablename__ = "customer_preferences"

    id = Column(String, primary_key=True, default=lambda: gen_id("pref"))
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, unique=True)
    preferred_method = Column(String, nullable=True)
    preferred_channel = Column(String, default="whatsapp")
    historical_payment_method = Column(String, nullable=True)
    historical_success_rate = Column(Float, default=0.8)
    avg_hours_to_pay = Column(Float, default=12.0)
    late_payment_rate = Column(Float, default=0.1)
    opted_out_channels = Column(JSON, default=list)

    customer = relationship("Customer", back_populates="preference")


class PaymentProvider(Base):
    __tablename__ = "payment_providers"

    id = Column(String, primary_key=True, default=lambda: gen_id("prv"))
    method = Column(String, nullable=False)  # pix|credit_card|debit_card|boleto|payment_link
    name = Column(String, nullable=False)
    status = Column(String, default="operational")  # operational|degraded|down
    base_cost_pct = Column(Float, default=1.0)
    fixed_fee = Column(Float, default=0.0)
    avg_settlement_hours = Column(Float, default=24.0)
    base_conversion = Column(Float, default=0.85)
    error_rate = Column(Float, default=0.02)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReceivableIntent(Base):
    __tablename__ = "receivable_intents"

    id = Column(String, primary_key=True, default=lambda: gen_id("int"))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="BRL")
    due_date = Column(DateTime, nullable=False)
    objective = Column(String, default="balanced")
    allowed_payment_methods = Column(JSON, default=list)
    forbidden_payment_methods = Column(JSON, default=list)
    max_cost_pct = Column(Float, nullable=True)
    max_risk = Column(String, default="medium")  # low|medium|high
    liquidity_need = Column(String, default="standard")  # urgent|standard|flexible
    status = Column(String, default="created")
    # created -> scored -> awaiting_approval -> executing -> awaiting_payment
    # -> confirmed -> settled | failed | cancelled
    idempotency_key = Column(String, unique=True, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    merchant = relationship("Merchant", back_populates="intents")
    customer = relationship("Customer")
    options = relationship("PaymentOption", back_populates="intent", cascade="all, delete-orphan")
    routes = relationship("PaymentRoute", back_populates="intent", cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="intent", uselist=False, cascade="all, delete-orphan")
    communications = relationship("CommunicationEvent", back_populates="intent", cascade="all, delete-orphan")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True, default=lambda: gen_id("risk"))
    intent_id = Column(String, ForeignKey("receivable_intents.id"), nullable=False)
    fraud_score = Column(Float, default=0.0)
    chargeback_score = Column(Float, default=0.0)
    risk_level = Column(String, default="low")  # low|medium|high
    model_version = Column(String, default="risk-heuristic-v1")
    created_at = Column(DateTime, default=datetime.utcnow)

    intent = relationship("ReceivableIntent", back_populates="risk_assessment")


class PaymentOption(Base):
    __tablename__ = "payment_options"

    id = Column(String, primary_key=True, default=lambda: gen_id("opt"))
    intent_id = Column(String, ForeignKey("receivable_intents.id"), nullable=False)
    method = Column(String, nullable=False)
    provider_id = Column(String, ForeignKey("payment_providers.id"), nullable=True)
    estimated_cost_pct = Column(Float, default=0.0)
    estimated_conversion = Column(Float, default=0.0)
    estimated_settlement_hours = Column(Float, default=0.0)
    estimated_risk = Column(Float, default=0.0)
    estimated_experience = Column(Float, default=0.0)
    preference_match = Column(Float, default=0.0)
    eligible = Column(Boolean, default=True)
    exclusion_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    intent = relationship("ReceivableIntent", back_populates="options")
    score = relationship("DecisionScore", back_populates="option", uselist=False, cascade="all, delete-orphan")
    provider = relationship("PaymentProvider")


class DecisionScore(Base):
    __tablename__ = "decision_scores"

    id = Column(String, primary_key=True, default=lambda: gen_id("scr"))
    option_id = Column(String, ForeignKey("payment_options.id"), nullable=False, unique=True)
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    weights_applied = Column(JSON, default=dict)
    breakdown = Column(JSON, default=dict)
    rank = Column(Integer, default=0)
    model_version = Column(String, default="decision-engine-v1")
    created_at = Column(DateTime, default=datetime.utcnow)

    option = relationship("PaymentOption", back_populates="score")


class ModelDecision(Base):
    __tablename__ = "model_decisions"

    id = Column(String, primary_key=True, default=lambda: gen_id("mdl"))
    intent_id = Column(String, ForeignKey("receivable_intents.id"), nullable=False)
    model_version = Column(String, default="decision-engine-v1")
    input_features = Column(JSON, default=dict)
    output = Column(JSON, default=dict)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class FallbackPlan(Base):
    __tablename__ = "fallback_plans"

    id = Column(String, primary_key=True, default=lambda: gen_id("fbp"))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    name = Column(String, default="default")
    sequence = Column(JSON, default=list)  # e.g. ["pix", "boleto", "credit_card"]
    max_hops = Column(Integer, default=2)
    is_default = Column(Boolean, default=True)


class RetryPolicy(Base):
    __tablename__ = "retry_policies"

    id = Column(String, primary_key=True, default=lambda: gen_id("rtp"))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    max_retries = Column(Integer, default=2)
    backoff_seconds = Column(Integer, default=30)
    is_default = Column(Boolean, default=True)


class PaymentRoute(Base):
    __tablename__ = "payment_routes"

    id = Column(String, primary_key=True, default=lambda: gen_id("rte"))
    intent_id = Column(String, ForeignKey("receivable_intents.id"), nullable=False)
    chosen_method = Column(String, nullable=False)
    provider_id = Column(String, ForeignKey("payment_providers.id"), nullable=True)
    mode = Column(String, default="recommendation")
    status = Column(String, default="pending")  # pending|confirmed|failed|fallback_triggered
    approved_by = Column(String, nullable=True)
    hop_index = Column(Integer, default=0)
    triggered_by = Column(String, default="approval")  # approval|autopilot|fallback|retry
    created_at = Column(DateTime, default=datetime.utcnow)

    intent = relationship("ReceivableIntent", back_populates="routes")
    attempts = relationship("PaymentAttempt", back_populates="route", cascade="all, delete-orphan")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id = Column(String, primary_key=True, default=lambda: gen_id("att"))
    route_id = Column(String, ForeignKey("payment_routes.id"), nullable=False)
    method = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending|confirmed|failed|expired
    provider_ref = Column(String, nullable=True)
    attempt_number = Column(Integer, default=1)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    failure_reason = Column(String, nullable=True)

    route = relationship("PaymentRoute", back_populates="attempts")
    settlement = relationship("Settlement", back_populates="attempt", uselist=False, cascade="all, delete-orphan")


class CommunicationEvent(Base):
    __tablename__ = "communication_events"

    id = Column(String, primary_key=True, default=lambda: gen_id("com"))
    intent_id = Column(String, ForeignKey("receivable_intents.id"), nullable=False)
    channel = Column(String, default="whatsapp")
    status = Column(String, default="sent")  # sent|delivered|opened|failed
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime, nullable=True)

    intent = relationship("ReceivableIntent", back_populates="communications")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(String, primary_key=True, default=lambda: gen_id("stl"))
    attempt_id = Column(String, ForeignKey("payment_attempts.id"), nullable=False, unique=True)
    gross_amount = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)
    expected_settlement_at = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempt = relationship("PaymentAttempt", back_populates="settlement")
    reconciliation = relationship("Reconciliation", back_populates="settlement", uselist=False, cascade="all, delete-orphan")


class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id = Column(String, primary_key=True, default=lambda: gen_id("rec"))
    settlement_id = Column(String, ForeignKey("settlements.id"), nullable=False, unique=True)
    matched = Column(Boolean, default=True)
    discrepancy_amount = Column(Float, default=0.0)
    reconciled_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)

    settlement = relationship("Settlement", back_populates="reconciliation")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: gen_id("aud"))
    actor = Column(String, nullable=False)  # e.g. "agent:orchestrator", "user:...", "system"
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    prev_hash = Column(String, nullable=True)
    hash = Column(String, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: gen_id("alr"))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=True)
    severity = Column(String, default="info")  # info|warning|critical
    category = Column(String, default="operational")  # operational|risk|model|provider
    message = Column(String, nullable=False)
    context = Column(JSON, default=dict)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
