"""Rule + ML Alert Engine (spec seção 36) — MVP scope covers the
feature-derived rules; forecast-based alerts (rain forecast, drought risk
from forecast) plug in once a forecast provider is configured for the
tenant (ProviderRouter.forecast)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import models

DEDUPE_WINDOW_KINDS = {
    "ndvi_anomaly",
    "soil_moisture",
    "yield_deterioration",
    "negative_margin",
}


def _upsert_alert(db: Session, field_id: str, kind: str, severity: str, message: str) -> None:
    existing = (
        db.query(models.Alert)
        .filter(models.Alert.field_id == field_id, models.Alert.kind == kind, models.Alert.acknowledged.is_(False))
        .first()
    )
    if existing:
        existing.message = message
        existing.severity = severity
        return
    db.add(models.Alert(field_id=field_id, kind=kind, severity=severity, message=message))


def evaluate_alerts(db: Session, field: models.Field, features: dict, prediction: dict, profitability: dict) -> None:
    if prediction["risk_level"] in ("high", "critical"):
        _upsert_alert(
            db,
            field.id,
            "ndvi_anomaly",
            "critical" if prediction["risk_level"] == "critical" else "warning",
            f"Vigor vegetativo (NDVI) anômalo detectado no talhão {field.name}.",
        )

    dry_days = features.get("consecutive_dry_days")
    if dry_days is not None and dry_days >= 12:
        _upsert_alert(
            db, field.id, "soil_moisture", "warning",
            f"{dry_days} dias consecutivos sem chuva registrados em {field.name}.",
        )

    if profitability["contribution_margin_per_ha"] < 0:
        _upsert_alert(
            db, field.id, "negative_margin", "critical",
            f"Margem de contribuição esperada negativa em {field.name} "
            f"(R$ {profitability['contribution_margin_per_ha']}/ha).",
        )

    historical_mean = features.get("historical_yield_mean_kg_ha")
    if historical_mean and prediction["yield_expected_kg_ha"] < historical_mean * 0.85:
        _upsert_alert(
            db, field.id, "yield_deterioration", "warning",
            f"Previsão de produtividade {round((1 - prediction['yield_expected_kg_ha'] / historical_mean) * 100, 1)}% "
            f"abaixo da média histórica em {field.name}.",
        )

    db.commit()
