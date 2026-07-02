"""Agente de Risco: heuristica deterministica de fraude e chargeback.

Em producao isto seria um modelo treinado (secao 9 do design doc). Para a
demo, usamos uma heuristica explicavel baseada em sinais disponiveis:
segmento do cliente, historico de sucesso/atraso, valor da transacao e
disponibilidade de historico (cliente novo = maior incerteza).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskResult:
    fraud_score: float  # 0..1, quanto maior, mais arriscado
    chargeback_score: float  # 0..1
    risk_level: str  # low|medium|high


RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def assess_risk(*, amount: float, segment: str, has_history: bool,
                 historical_success_rate: float, late_payment_rate: float) -> RiskResult:
    # Ticket alto e ausencia de historico aumentam o score de fraude.
    amount_factor = min(amount / 20000.0, 1.0) * 0.35
    novelty_factor = 0.0 if has_history else 0.30
    segment_factor = {"b2c": 0.10, "b2b_avulso": 0.15, "b2b_recurring": 0.02}.get(segment, 0.10)
    fraud_score = round(min(amount_factor + novelty_factor + segment_factor, 1.0), 3)

    # Chargeback correlaciona com baixa taxa de sucesso historica e atraso.
    base_cb = 0.05 if has_history else 0.12
    cb_from_history = (1 - historical_success_rate) * 0.4
    cb_from_late = late_payment_rate * 0.3
    chargeback_score = round(min(base_cb + cb_from_history + cb_from_late, 1.0), 3)

    composite = (fraud_score * 0.6) + (chargeback_score * 0.4)
    if composite < 0.25:
        level = "low"
    elif composite < 0.55:
        level = "medium"
    else:
        level = "high"

    return RiskResult(fraud_score=fraud_score, chargeback_score=chargeback_score, risk_level=level)


def exceeds_risk_appetite(risk_level: str, max_risk: str) -> bool:
    return RISK_ORDER[risk_level] > RISK_ORDER.get(max_risk, 1)


# Risco inerente por meio (chargeback é essencialmente um risco de cartão;
# Pix e boleto têm perfis de risco diferentes — estorno indevido é raro).
METHOD_RISK_MULTIPLIER = {
    "credit_card": 1.15,
    "debit_card": 0.85,
    "pix": 0.55,
    "boleto": 0.45,
    "payment_link": 1.0,
}


def method_risk_estimate(method: str, base_risk: RiskResult) -> float:
    base = (base_risk.fraud_score * 0.5) + (base_risk.chargeback_score * 0.5)
    multiplier = METHOD_RISK_MULTIPLIER.get(method, 1.0)
    return round(min(base * multiplier, 1.0), 3)
