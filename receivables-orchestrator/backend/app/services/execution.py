"""Servico de Roteamento de Pagamento + Retry + Fallback (secao 3/6 do design doc).

Orquestra a execucao de uma PaymentRoute, a resolucao assincrona simulada
de cada PaymentAttempt (via thread em background, analoga a um webhook real
chegando depois) e a cadeia de retry/fallback quando uma tentativa falha.
"""
from __future__ import annotations

import threading
from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.engine import fallback as fallback_engine
from app.engine import retry as retry_engine
from app.providers import simulator
from app.services import alerts, audit, reconciliation

MAX_EXPOSURE_GUARDRAIL_MSG = "valor da intencao excede max_exposure da politica — execucao automatica bloqueada"


def _get_provider(db: Session, method: str) -> models.PaymentProvider | None:
    return db.query(models.PaymentProvider).filter(models.PaymentProvider.method == method).first()


def _option_for(intent: models.ReceivableIntent, method: str) -> models.PaymentOption | None:
    return next((o for o in intent.options if o.method == method), None)


def create_route_and_attempt(db: Session, intent: models.ReceivableIntent, method: str, *,
                              mode: str, triggered_by: str, approved_by: str | None,
                              hop_index: int = 0) -> models.PaymentRoute:
    provider = _get_provider(db, method)
    route = models.PaymentRoute(
        intent_id=intent.id,
        chosen_method=method,
        provider_id=provider.id if provider else None,
        mode=mode,
        status="pending",
        approved_by=approved_by,
        hop_index=hop_index,
        triggered_by=triggered_by,
    )
    db.add(route)
    db.flush()

    charge = simulator.create_charge(method)
    attempt = models.PaymentAttempt(
        route_id=route.id,
        method=method,
        status="pending",
        provider_ref=charge.provider_ref,
        attempt_number=1,
        expires_at=charge.expires_at,
    )
    db.add(attempt)

    intent.status = "awaiting_payment"
    db.add(models.CommunicationEvent(intent_id=intent.id, channel="whatsapp", status="sent"))
    db.commit()
    db.refresh(route)
    db.refresh(attempt)

    audit.record(db, actor=f"agent:orchestrator" if triggered_by != "approval" else f"user:{approved_by}",
                 action="route_executed", entity_type="PaymentRoute", entity_id=route.id,
                 after={"method": method, "mode": mode, "triggered_by": triggered_by, "hop_index": hop_index})

    schedule_resolution(attempt.id)
    return route


def approve_and_execute(db: Session, intent: models.ReceivableIntent, method: str, approved_by: str) -> models.PaymentRoute:
    return create_route_and_attempt(db, intent, method, mode="recommendation", triggered_by="approval",
                                     approved_by=approved_by)


def maybe_autopilot(db: Session, intent: models.ReceivableIntent, policy: models.MerchantPolicy) -> models.PaymentRoute | None:
    """Aciona execucao automatica conforme o modo de operacao da politica
    (secao 4 do design doc). Retorna a rota criada, ou None se ficou em
    modo recomendacao aguardando aprovacao humana."""
    top_option = next((o for o in sorted(intent.options, key=lambda o: (o.score.rank if o.score else 999))
                        if o.eligible and o.score), None)
    if not top_option:
        return None

    mode = policy.operation_mode
    confidence = top_option.score.confidence
    threshold = policy.confidence_threshold

    if mode == "recommendation":
        return None
    if intent.amount > policy.max_exposure:
        alerts.raise_alert(db, merchant_id=intent.merchant_id, severity="warning", category="risk",
                            message=f"Intenção {intent.id} excede max_exposure ({policy.max_exposure}) — mantida em modo recomendação.",
                            context={"intent_id": intent.id, "amount": intent.amount})
        return None
    if top_option.estimated_risk >= 0.6:
        return None  # guardrail duro: nunca autopilot em risco alto, independente do modo

    if mode == "conservative" and confidence < max(threshold, 0.85):
        return None
    if mode in ("automatic", "assisted") and confidence < threshold:
        return None

    triggered_by = "autopilot" if mode in ("automatic", "conservative") else "assisted_rule"
    return create_route_and_attempt(db, intent, top_option.method, mode=mode, triggered_by=triggered_by,
                                     approved_by=None)


def schedule_resolution(attempt_id: str) -> None:
    delay = simulator.resolution_delay_seconds()
    t = threading.Timer(delay, _resolve_attempt_job, args=(attempt_id,))
    t.daemon = True
    t.start()


def _resolve_attempt_job(attempt_id: str) -> None:
    db = SessionLocal()
    try:
        resolve_attempt(db, attempt_id)
    finally:
        db.close()


def resolve_attempt(db: Session, attempt_id: str) -> models.PaymentAttempt | None:
    attempt = db.get(models.PaymentAttempt, attempt_id)
    if not attempt or attempt.status != "pending":
        return attempt

    route = attempt.route
    intent = route.intent
    option = _option_for(intent, attempt.method)
    provider = _get_provider(db, attempt.method)

    conversion_probability = option.estimated_conversion if option else 0.7
    error_rate = provider.error_rate if provider else 0.02

    success, failure_reason = simulator.resolve_outcome(
        method=attempt.method, conversion_probability=conversion_probability, provider_error_rate=error_rate
    )

    attempt.status = "confirmed" if success else "failed"
    attempt.failure_reason = failure_reason
    if success:
        attempt.confirmed_at = datetime.utcnow()
    db.commit()

    audit.record(db, actor=f"provider:{attempt.method}", action="attempt_resolved",
                 entity_type="PaymentAttempt", entity_id=attempt.id,
                 after={"status": attempt.status, "failure_reason": failure_reason})

    if success:
        route.status = "confirmed"
        intent.status = "confirmed"
        db.commit()
        reconciliation.create_settlement(db, attempt, provider)
        return attempt

    route.status = "failed"
    intent.status = "payment_failed"
    db.commit()

    if provider and error_rate > 0 and failure_reason == "erro_tecnico_provedor":
        alerts.raise_alert(db, merchant_id=intent.merchant_id, severity="warning", category="provider",
                            message=f"Erro técnico no provedor de {attempt.method} durante a tentativa {attempt.id}.",
                            context={"attempt_id": attempt.id, "method": attempt.method})

    _handle_retry_or_fallback(db, intent, route, attempt)
    return attempt


def _handle_retry_or_fallback(db: Session, intent: models.ReceivableIntent, route: models.PaymentRoute,
                               failed_attempt: models.PaymentAttempt) -> None:
    retry_policy = (
        db.query(models.RetryPolicy)
        .filter(models.RetryPolicy.merchant_id == intent.merchant_id, models.RetryPolicy.is_default.is_(True))
        .first()
    )
    max_retries = retry_policy.max_retries if retry_policy else 1

    if failed_attempt.attempt_number <= max_retries and failed_attempt.failure_reason != "expirado_sem_pagamento":
        next_number = failed_attempt.attempt_number + 1
        charge = simulator.create_charge(failed_attempt.method)
        new_attempt = models.PaymentAttempt(
            route_id=route.id, method=failed_attempt.method, status="pending",
            provider_ref=charge.provider_ref, attempt_number=next_number, expires_at=charge.expires_at,
        )
        db.add(new_attempt)
        route.status = "pending"
        intent.status = "awaiting_payment"
        db.commit()
        db.refresh(new_attempt)

        audit.record(db, actor="agent:orchestrator", action="retry_scheduled", entity_type="PaymentAttempt",
                     entity_id=new_attempt.id, after={"attempt_number": next_number, "method": failed_attempt.method})
        schedule_resolution(new_attempt.id)
        return

    apply_fallback(db, intent, route, failed_attempt.method)


def apply_fallback(db: Session, intent: models.ReceivableIntent, failed_route: models.PaymentRoute,
                    failed_method: str) -> models.PaymentRoute | None:
    plan = (
        db.query(models.FallbackPlan)
        .filter(models.FallbackPlan.merchant_id == intent.merchant_id, models.FallbackPlan.is_default.is_(True))
        .first()
    )
    sequence = plan.sequence if plan else ["pix", "boleto", "credit_card"]
    max_hops = plan.max_hops if plan else 2

    next_method = fallback_engine.next_fallback_method(sequence, failed_method, failed_route.hop_index, max_hops)
    if not next_method:
        intent.status = "failed"
        db.commit()
        alerts.raise_alert(db, merchant_id=intent.merchant_id, severity="critical", category="operational",
                            message=f"Fallback esgotado para a intenção {intent.id} — nenhuma opção restante.",
                            context={"intent_id": intent.id})
        audit.record(db, actor="agent:orchestrator", action="fallback_exhausted", entity_type="ReceivableIntent",
                     entity_id=intent.id, after={"failed_method": failed_method})
        return None

    option = _option_for(intent, next_method)
    if option and not option.eligible:
        # tenta o proximo da sequencia recursivamente
        failed_route.hop_index += 1
        db.commit()
        return apply_fallback(db, intent, failed_route, next_method)

    audit.record(db, actor="agent:orchestrator", action="fallback_applied", entity_type="ReceivableIntent",
                 entity_id=intent.id, before={"from_method": failed_method}, after={"to_method": next_method})

    new_route = create_route_and_attempt(
        db, intent, next_method, mode=failed_route.mode, triggered_by="fallback",
        approved_by=failed_route.approved_by, hop_index=failed_route.hop_index + 1,
    )
    return new_route


def apply_webhook_result(db: Session, route_id: str, status: str, failure_reason: str | None = None) -> models.PaymentAttempt | None:
    """Aplica o resultado de um webhook de provedor explicito, sobrepondo a
    resolucao simulada automatica (util para testes e para demonstrar a
    superficie de API descrita na secao 7 do design doc)."""
    route = db.get(models.PaymentRoute, route_id)
    if not route:
        return None
    attempt = next((a for a in sorted(route.attempts, key=lambda a: a.attempt_number, reverse=True)
                     if a.status == "pending"), None)
    if not attempt:
        return None

    attempt.status = "confirmed" if status == "confirmed" else "failed"
    attempt.failure_reason = None if status == "confirmed" else (failure_reason or "webhook_failed")
    if status == "confirmed":
        attempt.confirmed_at = datetime.utcnow()
    db.commit()

    audit.record(db, actor="webhook:provider", action="webhook_received", entity_type="PaymentAttempt",
                 entity_id=attempt.id, after={"status": attempt.status})

    intent = route.intent
    if status == "confirmed":
        route.status = "confirmed"
        intent.status = "confirmed"
        db.commit()
        provider = _get_provider(db, attempt.method)
        reconciliation.create_settlement(db, attempt, provider)
    else:
        route.status = "failed"
        intent.status = "payment_failed"
        db.commit()
        _handle_retry_or_fallback(db, intent, route, attempt)

    return attempt


def force_retry(db: Session, intent: models.ReceivableIntent) -> models.PaymentAttempt | None:
    last_route = intent.routes[-1] if intent.routes else None
    if not last_route:
        return None
    charge = simulator.create_charge(last_route.chosen_method)
    next_number = (last_route.attempts[-1].attempt_number + 1) if last_route.attempts else 1
    attempt = models.PaymentAttempt(
        route_id=last_route.id, method=last_route.chosen_method, status="pending",
        provider_ref=charge.provider_ref, attempt_number=next_number, expires_at=charge.expires_at,
    )
    db.add(attempt)
    intent.status = "awaiting_payment"
    last_route.status = "pending"
    db.commit()
    db.refresh(attempt)
    audit.record(db, actor="user:manual", action="manual_retry", entity_type="PaymentAttempt",
                 entity_id=attempt.id, after={"attempt_number": next_number})
    schedule_resolution(attempt.id)
    return attempt
