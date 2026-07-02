"""Agregacoes para os dashboards (secao 2/16/17 do design doc)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app import models, schemas


def compute_metrics(db: Session, merchant_id: str, period_days: int = 30) -> schemas.MetricsOut:
    since = datetime.utcnow() - timedelta(days=period_days)

    intents = (
        db.query(models.ReceivableIntent)
        .filter(models.ReceivableIntent.merchant_id == merchant_id, models.ReceivableIntent.created_at >= since)
        .all()
    )
    total_intents = len(intents)
    confirmed_intents = sum(1 for i in intents if i.status in ("confirmed", "settled", "settled_pending_reconciliation"))
    conversion_rate = round(confirmed_intents / total_intents, 4) if total_intents else 0.0

    all_routes = [r for i in intents for r in i.routes]
    all_attempts = [a for r in all_routes for a in r.attempts]

    settlements = [a.settlement for a in all_attempts if a.settlement]
    avg_cost_pct = 0.0
    if settlements:
        avg_cost_pct = round(sum((s.fee / s.gross_amount * 100) for s in settlements if s.gross_amount) / len(settlements), 3)

    confirmed_attempts = [a for a in all_attempts if a.status == "confirmed" and a.confirmed_at]
    time_to_payment = []
    for a in confirmed_attempts:
        route = a.route
        delta_hours = (a.confirmed_at - route.created_at).total_seconds() / 3600
        time_to_payment.append(delta_hours)
    avg_time_to_payment_hours = round(sum(time_to_payment) / len(time_to_payment), 3) if time_to_payment else 0.0

    fallback_intents = sum(1 for i in intents if any(r.triggered_by == "fallback" for r in i.routes))
    fallback_rate = round(fallback_intents / total_intents, 4) if total_intents else 0.0

    retried = [a for a in all_attempts if a.attempt_number > 1]
    retry_success = [a for a in retried if a.status == "confirmed"]
    retry_success_rate = round(len(retry_success) / len(retried), 4) if retried else 0.0

    risk_assessments = [i.risk_assessment for i in intents if i.risk_assessment]
    chargeback_rate_proxy = (
        round(sum(r.chargeback_score for r in risk_assessments) / len(risk_assessments), 4) if risk_assessments else 0.0
    )

    conv_by_method_attempts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for a in all_attempts:
        conv_by_method_attempts[a.method][1] += 1
        if a.status == "confirmed":
            conv_by_method_attempts[a.method][0] += 1
    conversion_by_method = {
        m: round(v[0] / v[1], 4) if v[1] else 0.0 for m, v in conv_by_method_attempts.items()
    }

    cost_by_method: dict[str, list[float]] = defaultdict(list)
    volume_by_method: dict[str, float] = defaultdict(float)
    for a in all_attempts:
        if a.settlement:
            cost_by_method[a.method].append(a.settlement.fee / a.settlement.gross_amount * 100 if a.settlement.gross_amount else 0)
            volume_by_method[a.method] += a.settlement.gross_amount

    cost_by_method_avg = {m: round(sum(v) / len(v), 3) for m, v in cost_by_method.items()}

    return schemas.MetricsOut(
        merchant_id=merchant_id,
        period_days=period_days,
        total_intents=total_intents,
        conversion_rate=conversion_rate,
        avg_cost_pct=avg_cost_pct,
        avg_time_to_payment_hours=avg_time_to_payment_hours,
        fallback_rate=fallback_rate,
        retry_success_rate=retry_success_rate,
        chargeback_rate_proxy=chargeback_rate_proxy,
        conversion_by_method=conversion_by_method,
        cost_by_method=cost_by_method_avg,
        volume_by_method=dict(volume_by_method),
    )


def list_settlements(db: Session, merchant_id: str, period_days: int = 30) -> list[schemas.SettlementOut]:
    since = datetime.utcnow() - timedelta(days=period_days)
    intents = (
        db.query(models.ReceivableIntent)
        .filter(models.ReceivableIntent.merchant_id == merchant_id, models.ReceivableIntent.created_at >= since)
        .all()
    )
    out = []
    for i in intents:
        for r in i.routes:
            for a in r.attempts:
                if a.settlement:
                    s = a.settlement
                    out.append(schemas.SettlementOut(
                        id=s.id, attempt_id=a.id, gross_amount=s.gross_amount, fee=s.fee, net_amount=s.net_amount,
                        expected_settlement_at=s.expected_settlement_at, settled_at=s.settled_at,
                        reconciled=bool(s.reconciliation and s.reconciliation.matched),
                        discrepancy_amount=s.reconciliation.discrepancy_amount if s.reconciliation else 0.0,
                    ))
    return sorted(out, key=lambda s: s.settled_at or datetime.min, reverse=True)
