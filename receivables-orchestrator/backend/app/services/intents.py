"""Agente Orquestrador de Recebimento: cria a intencao, consulta contexto
(risco/custo/liquidez/preferencia), calcula as opcoes e aciona o motor de
scoring — implementando as etapas 1-6 da jornada (secao 3 do design doc)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app import models, schemas
from app.engine import explain as explain_engine
from app.engine import risk as risk_engine
from app.engine import rules as rules_engine
from app.engine import scoring as scoring_engine
from app.services import alerts, audit

AVAILABLE_METHODS = ["pix", "credit_card", "boleto"]


@dataclass
class OptionBundle:
    method: str
    provider: models.PaymentProvider | None
    eligible: bool
    exclusion_reason: str | None
    estimate: scoring_engine.OptionEstimate | None
    scored: scoring_engine.ScoredOption | None


def _get_default_policy(db: Session, merchant_id: str) -> models.MerchantPolicy:
    policy = (
        db.query(models.MerchantPolicy)
        .filter(models.MerchantPolicy.merchant_id == merchant_id, models.MerchantPolicy.is_default.is_(True))
        .first()
    )
    if not policy:
        policy = db.query(models.MerchantPolicy).filter(models.MerchantPolicy.merchant_id == merchant_id).first()
    return policy


def _get_or_create_preference(db: Session, customer: models.Customer) -> models.CustomerPreference:
    if customer.preference:
        return customer.preference
    pref = models.CustomerPreference(customer_id=customer.id)
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


def build_option_bundles(db: Session, intent: models.ReceivableIntent, weights: dict) -> list[OptionBundle]:
    customer = intent.customer
    preference = _get_or_create_preference(db, customer)
    policy = _get_default_policy(db, intent.merchant_id)

    has_history = bool(preference.historical_payment_method)
    risk_result = risk_engine.assess_risk(
        amount=intent.amount,
        segment=customer.segment,
        has_history=has_history,
        historical_success_rate=preference.historical_success_rate,
        late_payment_rate=preference.late_payment_rate,
    )

    existing_risk = intent.risk_assessment
    if existing_risk:
        existing_risk.fraud_score = risk_result.fraud_score
        existing_risk.chargeback_score = risk_result.chargeback_score
        existing_risk.risk_level = risk_result.risk_level
    else:
        db.add(models.RiskAssessment(
            intent_id=intent.id,
            fraud_score=risk_result.fraud_score,
            chargeback_score=risk_result.chargeback_score,
            risk_level=risk_result.risk_level,
        ))
    db.commit()

    providers = {
        p.method: p
        for p in db.query(models.PaymentProvider).filter(models.PaymentProvider.method.in_(AVAILABLE_METHODS)).all()
    }

    eligibility = rules_engine.filter_eligible_methods(
        intent_allowed=intent.allowed_payment_methods or [],
        intent_forbidden=intent.forbidden_payment_methods or [],
        policy_allowed=policy.allowed_methods if policy else AVAILABLE_METHODS,
        available_methods=list(providers.keys()),
    )
    eligibility_map = {e.method: e for e in eligibility}

    data_completeness = 1.0 if has_history else 0.5
    bundles: list[OptionBundle] = []

    for method, provider in providers.items():
        elig = eligibility_map.get(method)
        reason = elig.reason if elig else None
        eligible = elig.eligible if elig else False

        method_risk = risk_engine.method_risk_estimate(method, risk_result)
        method_risk_level = "low" if method_risk < 0.25 else ("medium" if method_risk < 0.55 else "high")

        estimate = scoring_engine.estimate_option(
            method=method,
            provider_id=provider.id,
            provider_name=provider.name,
            base_cost_pct=provider.base_cost_pct,
            fixed_fee=provider.fixed_fee,
            amount=intent.amount,
            base_conversion=provider.base_conversion,
            provider_status=provider.status,
            avg_settlement_hours=provider.avg_settlement_hours,
            method_risk=method_risk,
            preferred_method=preference.preferred_method,
            historical_payment_method=preference.historical_payment_method,
            liquidity_need=intent.liquidity_need,
        )

        if eligible:
            reason = reason or rules_engine.provider_check(provider.status)
        if eligible and reason is None:
            reason = rules_engine.cost_check(estimate.estimated_cost_pct, intent.max_cost_pct)
        if eligible and reason is None:
            exceeds = risk_engine.exceeds_risk_appetite(method_risk_level, intent.max_risk)
            reason = rules_engine.risk_check(method_risk, exceeds)
        if reason is not None:
            eligible = False

        scored = None
        if eligible:
            scored = scoring_engine.score_option(estimate, weights, data_completeness)

        bundles.append(OptionBundle(method=method, provider=provider, eligible=eligible,
                                     exclusion_reason=reason, estimate=estimate, scored=scored))

    return bundles


def persist_options(db: Session, intent: models.ReceivableIntent, bundles: list[OptionBundle], weights: dict) -> list[models.PaymentOption]:
    # limpa opcoes anteriores (idempotente por intent)
    db.query(models.PaymentOption).filter(models.PaymentOption.intent_id == intent.id).delete()
    db.commit()

    ranked = sorted(
        [b for b in bundles if b.eligible and b.scored],
        key=lambda b: b.scored.score,
        reverse=True,
    )
    rank_map = {b.method: i + 1 for i, b in enumerate(ranked)}

    persisted = []
    for b in bundles:
        est = b.estimate
        option = models.PaymentOption(
            intent_id=intent.id,
            method=b.method,
            provider_id=b.provider.id if b.provider else None,
            estimated_cost_pct=est.estimated_cost_pct if est else 0,
            estimated_conversion=est.estimated_conversion if est else 0,
            estimated_settlement_hours=est.estimated_settlement_hours if est else 0,
            estimated_risk=est.estimated_risk if est else 0,
            estimated_experience=est.estimated_experience if est else 0,
            preference_match=est.preference_match if est else 0,
            eligible=b.eligible,
            exclusion_reason=b.exclusion_reason,
        )
        db.add(option)
        db.flush()

        if b.eligible and b.scored:
            db.add(models.DecisionScore(
                option_id=option.id,
                score=b.scored.score,
                confidence=b.scored.confidence,
                weights_applied=weights,
                breakdown=b.scored.breakdown,
                rank=rank_map.get(b.method, 0),
            ))
        persisted.append(option)

    db.commit()
    return persisted


def create_intent(db: Session, payload: schemas.ReceivableIntentIn) -> models.ReceivableIntent:
    if payload.idempotency_key:
        existing = db.query(models.ReceivableIntent).filter(
            models.ReceivableIntent.idempotency_key == payload.idempotency_key
        ).first()
        if existing:
            return existing

    intent = models.ReceivableIntent(
        merchant_id=payload.merchant_id,
        customer_id=payload.customer_id,
        amount=payload.amount,
        currency=payload.currency,
        due_date=payload.due_date,
        objective=payload.objective,
        allowed_payment_methods=payload.allowed_payment_methods,
        forbidden_payment_methods=payload.forbidden_payment_methods,
        max_cost_pct=payload.max_cost,
        max_risk=payload.max_risk,
        liquidity_need=payload.liquidity_need,
        metadata_json=payload.metadata,
        idempotency_key=payload.idempotency_key,
        status="created",
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)

    audit.record(db, actor="agent:orchestrator", action="intent_created", entity_type="ReceivableIntent",
                 entity_id=intent.id, after={"amount": intent.amount, "objective": intent.objective})

    run_decision_engine(db, intent)
    return intent


def run_decision_engine(db: Session, intent: models.ReceivableIntent) -> list[models.PaymentOption]:
    policy = _get_default_policy(db, intent.merchant_id)
    custom_weights = policy.weights if (policy and policy.objective == intent.objective) else None
    weights = scoring_engine.resolve_weights(intent.objective, custom_weights)

    bundles = build_option_bundles(db, intent, weights)
    options = persist_options(db, intent, bundles, weights)

    eligible_count = sum(1 for b in bundles if b.eligible)
    top = None
    if eligible_count:
        best = max((b for b in bundles if b.eligible and b.scored), key=lambda b: b.scored.score)
        top = best

    db.add(models.ModelDecision(
        intent_id=intent.id,
        model_version="decision-engine-v1",
        input_features={
            "amount": intent.amount,
            "objective": intent.objective,
            "max_cost": intent.max_cost_pct,
            "max_risk": intent.max_risk,
            "liquidity_need": intent.liquidity_need,
            "weights": weights,
        },
        output={
            "eligible_count": eligible_count,
            "top_method": top.method if top else None,
            "top_score": top.scored.score if top else None,
        },
    ))

    intent.status = "scored" if eligible_count else "no_eligible_option"
    db.commit()

    if eligible_count == 0:
        alerts.raise_alert(db, merchant_id=intent.merchant_id, severity="critical", category="operational",
                            message=f"Intenção {intent.id} não teve nenhuma opção de pagamento elegível.",
                            context={"intent_id": intent.id})
    elif top and top.scored.confidence < 0.5:
        alerts.raise_alert(db, merchant_id=intent.merchant_id, severity="warning", category="model",
                            message=f"Decisão de baixa confiança ({top.scored.confidence:.0%}) para a intenção {intent.id}.",
                            context={"intent_id": intent.id, "method": top.method})

    audit.record(db, actor="agent:orchestrator", action="decision_scored", entity_type="ReceivableIntent",
                 entity_id=intent.id, after={"eligible_count": eligible_count, "top_method": top.method if top else None})

    return options


def to_option_score_out(option: models.PaymentOption) -> schemas.OptionScoreOut:
    return schemas.OptionScoreOut(
        method=option.method,
        provider_name=option.provider.name if option.provider else None,
        eligible=option.eligible,
        exclusion_reason=option.exclusion_reason,
        estimated_cost_pct=option.estimated_cost_pct,
        estimated_conversion=option.estimated_conversion,
        estimated_settlement_hours=option.estimated_settlement_hours,
        estimated_risk=option.estimated_risk,
        estimated_experience=option.estimated_experience,
        preference_match=option.preference_match,
        score=option.score.score if option.score else None,
        confidence=option.score.confidence if option.score else None,
        rank=option.score.rank if option.score else None,
    )


def get_recommendation(db: Session, intent: models.ReceivableIntent) -> schemas.RecommendationOut:
    policy = _get_default_policy(db, intent.merchant_id)
    options = sorted(intent.options, key=lambda o: (o.score.rank if o.score else 999))
    out_options = [to_option_score_out(o) for o in options]
    top_eligible = next((o for o in options if o.eligible and o.score), None)

    return schemas.RecommendationOut(
        intent_id=intent.id,
        status=intent.status,
        model_version="decision-engine-v1",
        recommended_method=top_eligible.method if top_eligible else None,
        operation_mode=policy.operation_mode if policy else "recommendation",
        options=out_options,
    )


def build_explanation(db: Session, intent: models.ReceivableIntent) -> schemas.ExplanationOut:
    options = sorted(intent.options, key=lambda o: (o.score.rank if o.score else 999))
    top = next((o for o in options if o.eligible and o.score), None)

    all_dicts = [
        {
            "method": o.method,
            "eligible": o.eligible,
            "exclusion_reason": o.exclusion_reason,
            "estimated_cost_pct": o.estimated_cost_pct,
            "estimated_conversion": o.estimated_conversion,
            "estimated_settlement_hours": o.estimated_settlement_hours,
            "score": o.score.score if o.score else None,
        }
        for o in options
    ]

    weights = options[0].score.weights_applied if options and options[0].score else {}
    if top:
        chosen = {
            "method": top.method,
            "score": top.score.score,
            "confidence": top.score.confidence,
            "estimated_conversion": top.estimated_conversion,
            "estimated_cost_pct": top.estimated_cost_pct,
            "estimated_settlement_hours": top.estimated_settlement_hours,
        }
        reason_summary = explain_engine.build_reason_summary(chosen, weights or {})
        discarded = explain_engine.build_discarded(all_dicts, top.method)
    else:
        chosen = None
        reason_summary = "Nenhuma opção elegível foi encontrada para esta intenção."
        discarded = explain_engine.build_discarded(all_dicts, "__none__")

    audiences = explain_engine.build_audience_explanations(
        intent={"id": intent.id, "amount": intent.amount}, chosen=chosen, discarded=discarded, weights=weights or {}
    )

    return schemas.ExplanationOut(
        intent_id=intent.id,
        chosen_method=top.method if top else None,
        reason_summary=reason_summary,
        discarded_options=discarded,
        weights_applied=weights or {},
        audiences=[schemas.ExplanationAudienceOut(**a) for a in audiences],
    )
