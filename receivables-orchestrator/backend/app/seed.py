"""Dados de demonstracao: 2 estabelecimentos piloto, clientes com
historicos variados, provedores simulados e politicas distintas — o
suficiente para exercitar todos os modos de operacao descritos na secao 4
do design doc."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import models


def seed_if_empty(db: Session) -> None:
    if db.query(models.Merchant).count() > 0:
        return

    # ---------- Provedores (secao 6) ----------
    pix = models.PaymentProvider(method="pix", name="PSP Pix Demo", status="operational",
                                  base_cost_pct=0.99, fixed_fee=0.0, avg_settlement_hours=0.5,
                                  base_conversion=0.90, error_rate=0.01)
    credit_card = models.PaymentProvider(method="credit_card", name="Adquirente Cartão Demo", status="operational",
                                          base_cost_pct=3.49, fixed_fee=0.39, avg_settlement_hours=30,
                                          base_conversion=0.78, error_rate=0.03)
    boleto = models.PaymentProvider(method="boleto", name="Banco Emissor Boleto Demo", status="operational",
                                     base_cost_pct=1.49, fixed_fee=2.90, avg_settlement_hours=48,
                                     base_conversion=0.72, error_rate=0.01)
    db.add_all([pix, credit_card, boleto])
    db.commit()

    # ---------- Merchant 1: e-commerce B2C, modo recomendacao ----------
    m1 = models.Merchant(name="Nimbus Comércio Digital", document="12.345.678/0001-90", segment="e-commerce",
                          api_key="demo_nimbus_key")
    db.add(m1)
    db.commit()

    p1 = models.MerchantPolicy(merchant_id=m1.id, name="Política padrão — Nimbus", objective="balanced",
                                weights={"conversion": 0.22, "cost": 0.22, "risk": 0.22, "liquidity": 0.14,
                                         "experience": 0.12, "preference": 0.08},
                                max_exposure=8000.0, allowed_methods=["pix", "credit_card", "boleto"],
                                operation_mode="recommendation", confidence_threshold=0.55, is_default=True)
    db.add(p1)
    db.add(models.FallbackPlan(merchant_id=m1.id, name="default", sequence=["pix", "boleto", "credit_card"],
                                max_hops=2, is_default=True))
    db.add(models.RetryPolicy(merchant_id=m1.id, max_retries=1, backoff_seconds=20, is_default=True))

    nimbus_customers = [
        ("Ana Beatriz Costa", "111.111.111-11", "b2c", "pix", "pix", 0.95, 4.0, 0.02),
        ("Carlos Eduardo Lima", "222.222.222-22", "b2c", None, None, 0.80, 20.0, 0.15),
        ("Fernanda Souza", "333.333.333-33", "b2c", "credit_card", "credit_card", 0.88, 10.0, 0.08),
        ("Marcos Paulo Rocha", "444.444.444-44", "b2c", "boleto", "boleto", 0.70, 40.0, 0.25),
    ]
    for name, doc, seg, pref, hist, succ, hours, late in nimbus_customers:
        c = models.Customer(merchant_id=m1.id, name=name, document=doc, segment=seg,
                             contact_phone="+55 11 90000-0000", contact_email=f"{name.split()[0].lower()}@exemplo.com")
        db.add(c)
        db.flush()
        db.add(models.CustomerPreference(customer_id=c.id, preferred_method=pref, preferred_channel="whatsapp",
                                          historical_payment_method=hist, historical_success_rate=succ,
                                          avg_hours_to_pay=hours, late_payment_rate=late))

    # ---------- Merchant 2: consultoria B2B recorrente, modo assistido ----------
    m2 = models.Merchant(name="Vetor Consultoria Empresarial", document="98.765.432/0001-10", segment="b2b_services",
                          api_key="demo_vetor_key")
    db.add(m2)
    db.commit()

    p2 = models.MerchantPolicy(merchant_id=m2.id, name="Política padrão — Vetor", objective="minimize_cost",
                                weights={"conversion": 0.15, "cost": 0.45, "risk": 0.15, "liquidity": 0.10,
                                         "experience": 0.05, "preference": 0.10},
                                max_exposure=25000.0, allowed_methods=["pix", "boleto", "credit_card"],
                                operation_mode="assisted", confidence_threshold=0.6, is_default=True)
    db.add(p2)
    db.add(models.FallbackPlan(merchant_id=m2.id, name="default", sequence=["pix", "boleto", "credit_card"],
                                max_hops=2, is_default=True))
    db.add(models.RetryPolicy(merchant_id=m2.id, max_retries=1, backoff_seconds=30, is_default=True))

    vetor_customers = [
        ("Construtora Horizonte Ltda", "11.222.333/0001-44", "b2b_recurring", "boleto", "boleto", 0.92, 30.0, 0.05),
        ("Studio Criativo Aurora", "22.333.444/0001-55", "b2b_recurring", "pix", "pix", 0.97, 6.0, 0.01),
        ("Distribuidora Sul Ltda", "33.444.555/0001-66", "b2b_avulso", None, None, 0.75, 48.0, 0.18),
    ]
    for name, doc, seg, pref, hist, succ, hours, late in vetor_customers:
        c = models.Customer(merchant_id=m2.id, name=name, document=doc, segment=seg,
                             contact_phone="+55 21 90000-0000", contact_email=f"financeiro@{name.split()[0].lower()}.com.br")
        db.add(c)
        db.flush()
        db.add(models.CustomerPreference(customer_id=c.id, preferred_method=pref, preferred_channel="email",
                                          historical_payment_method=hist, historical_success_rate=succ,
                                          avg_hours_to_pay=hours, late_payment_rate=late))

    db.commit()
