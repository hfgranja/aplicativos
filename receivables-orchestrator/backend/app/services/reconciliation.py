"""Servico de Liquidacao e Conciliacao (secao 3/6 do design doc)."""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app import models
from app.services import alerts, audit

RECONCILIATION_TOLERANCE = 0.02  # R$ 0,02 de tolerancia de matching


def create_settlement(db: Session, attempt: models.PaymentAttempt, provider: models.PaymentProvider | None) -> models.Settlement:
    intent = attempt.route.intent
    gross = intent.amount
    cost_pct = provider.base_cost_pct if provider else 1.0
    fixed_fee = provider.fixed_fee if provider else 0.0
    fee = round(gross * (cost_pct / 100) + fixed_fee, 2)
    net = round(gross - fee, 2)
    settlement_hours = provider.avg_settlement_hours if provider else 24.0

    settlement = models.Settlement(
        attempt_id=attempt.id,
        gross_amount=gross,
        fee=fee,
        net_amount=net,
        expected_settlement_at=datetime.utcnow() + timedelta(hours=settlement_hours),
        settled_at=datetime.utcnow(),
    )
    db.add(settlement)
    db.flush()

    # Conciliacao automatica: na grande maioria dos casos o matching e
    # perfeito; ocasionalmente simulamos uma pequena divergencia para
    # exercitar a fila de excecao (secao 16/21 do design doc).
    discrepancy = 0.0
    matched = True
    if random.random() < 0.06:
        discrepancy = round(random.uniform(0.5, 15.0), 2)
        matched = False

    reconciliation = models.Reconciliation(
        settlement_id=settlement.id,
        matched=matched,
        discrepancy_amount=discrepancy,
        reconciled_at=datetime.utcnow() if matched else None,
    )
    db.add(reconciliation)
    intent.status = "settled" if matched else "settled_pending_reconciliation"
    db.commit()
    db.refresh(settlement)

    audit.record(db, actor="agent:conciliacao", action="settlement_created", entity_type="Settlement",
                 entity_id=settlement.id, after={"gross": gross, "fee": fee, "net": net, "matched": matched})

    if not matched:
        alerts.raise_alert(db, merchant_id=intent.merchant_id, severity="warning", category="operational",
                            message=f"Divergência de conciliação de R$ {discrepancy:.2f} na liquidação {settlement.id}.",
                            context={"settlement_id": settlement.id, "discrepancy": discrepancy})

    return settlement


def resolve_exception(db: Session, settlement_id: str, notes: str = "ajustado manualmente") -> models.Reconciliation | None:
    settlement = db.get(models.Settlement, settlement_id)
    if not settlement or not settlement.reconciliation:
        return None
    rec = settlement.reconciliation
    rec.matched = True
    rec.reconciled_at = datetime.utcnow()
    rec.notes = notes
    db.commit()
    audit.record(db, actor="user:manual", action="reconciliation_resolved", entity_type="Reconciliation",
                 entity_id=rec.id, after={"notes": notes})
    return rec
