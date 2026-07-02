"""Camada de integracao com provedores (secao 6 do design doc).

Em producao estes seriam clientes reais de PSP Pix, adquirente de cartao e
banco/agregador de boleto. Nesta demo, simulamos o comportamento externo
(criacao de cobranca, expiracao, confirmacao probabilistica) para que o
motor de orquestracao, fallback e retry possam ser exercitados de ponta a
ponta sem credenciais de producao.
"""
from __future__ import annotations

import os
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

SIM_MIN_SECONDS = int(os.getenv("SIM_MIN_RESOLUTION_SECONDS", "2"))
SIM_MAX_SECONDS = int(os.getenv("SIM_MAX_RESOLUTION_SECONDS", "6"))

# Prazo de expiracao "real" exibido ao usuario (nao é o tempo de simulacao).
METHOD_EXPIRY_MINUTES = {
    "pix": 30,
    "credit_card": 15,
    "debit_card": 15,
    "boleto": 60 * 24 * 3,  # 3 dias uteis
    "payment_link": 60 * 24,
}

FAILURE_REASONS = {
    "pix": ["expirado_sem_pagamento", "chave_pix_invalida"],
    "credit_card": ["cartao_recusado", "saldo_insuficiente", "antifraude_bloqueou"],
    "debit_card": ["cartao_recusado", "saldo_insuficiente"],
    "boleto": ["expirado_sem_pagamento"],
    "payment_link": ["expirado_sem_pagamento"],
}


@dataclass
class ChargeResult:
    provider_ref: str
    expires_at: datetime


def create_charge(method: str) -> ChargeResult:
    ref = f"prov_{method}_{uuid.uuid4().hex[:12]}"
    minutes = METHOD_EXPIRY_MINUTES.get(method, 60)
    return ChargeResult(provider_ref=ref, expires_at=datetime.utcnow() + timedelta(minutes=minutes))


def resolution_delay_seconds() -> int:
    return random.randint(SIM_MIN_SECONDS, SIM_MAX_SECONDS)


def resolve_outcome(*, method: str, conversion_probability: float, provider_error_rate: float) -> tuple[bool, str | None]:
    """Sorteia o desfecho da tentativa combinando propensao de pagamento do
    cliente com a taxa de erro tecnico do provedor."""
    roll = random.random()
    if roll < provider_error_rate:
        return False, "erro_tecnico_provedor"
    success = random.random() < conversion_probability
    if success:
        return True, None
    reason = random.choice(FAILURE_REASONS.get(method, ["recusado"]))
    return False, reason


def antifraude_score(*, amount: float, has_history: bool) -> float:
    """Simula um provedor de antifraude terceiro (secao 6)."""
    base = 0.05 + (0.0 if has_history else 0.10)
    base += min(amount / 50000.0, 0.2)
    return round(min(base, 1.0), 3)
