"""Orquestra o pipeline completo para um talhão (spec seção 70):

DATA -> INGESTION -> FEATURE STORE -> FENOLOGIA -> BALANÇO HÍDRICO ->
ML PREDICTION -> DIAGNÓSTICO AGRONÔMICO -> ECONOMIC -> DECISION ->
RECOMMENDATION (com dose) -> YIELD GAP -> EXPLAINABILITY

Routers chamam este módulo em vez de tocar providers/ml/services
diretamente, então todos os endpoints de leitura permanecem consistentes.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import models
from app.ml.yield_model import predict_yield
from app.providers.agriculture.ibge_provider import IbgeProvider
from app.providers.base import ProviderUnavailableError
from app.services import (
    agronomy_engine,
    alert_engine,
    confidence_engine,
    decision_engine,
    economic_engine,
    feature_engineering,
    ingestion,
    phenology as phenology_service,
    water_balance as water_balance_service,
    yield_gap as yield_gap_service,
)

logger = logging.getLogger("agroprofit.analysis")

_ibge_provider = IbgeProvider()
_ibge_cache: dict[tuple[str, str], float | None] = {}


def _regional_benchmark(db: Session, field: models.Field) -> float | None:
    """Benchmark municipal IBGE (contexto de yield gap) — best-effort, cache
    em processo, nunca bloqueia a análise (spec 4.12/51)."""
    farm = db.query(models.Farm).filter(models.Farm.id == field.farm_id).first()
    if not farm or not farm.ibge_municipality_code or not field.crop:
        return None
    key = (field.crop, farm.ibge_municipality_code)
    if key in _ibge_cache:
        return _ibge_cache[key]
    benchmark = None
    try:
        year = datetime.now(timezone.utc).year - 1
        result = _ibge_provider.municipal_yield(field.crop, farm.ibge_municipality_code, year)
        benchmark = result.get("average_yield_kg_ha")
    except ProviderUnavailableError as exc:
        logger.info("ibge benchmark unavailable: %s", exc)
    _ibge_cache[key] = benchmark
    return benchmark


def run_field_analysis(db: Session, field: models.Field, persist: bool = True) -> dict:
    ingestion.ensure_field_data_ingested(db, field)
    features = feature_engineering.build_field_features(db, field)

    # Camadas agronômicas: fenologia (GDD) e balanço hídrico (FAO-56)
    phenology = phenology_service.compute_phenology(db, field)
    water_balance = water_balance_service.compute_water_balance(db, field)
    if water_balance.get("available"):
        features["water_stress_index"] = water_balance["water_stress_index"]
        features["water_balance_fao56_mm"] = water_balance["cumulative_balance_mm"]

    prediction = predict_yield(field.crop, features)
    confidence_score, confidence_tier = confidence_engine.compute_confidence(features)

    forecast_rows = ingestion.ensure_forecast_ingested(db, field)

    agronomic_actions = agronomy_engine.evaluate(
        features=features,
        phenology=phenology,
        water_balance=water_balance,
        forecast_rows=forecast_rows,
        crop=field.crop,
        planting_date=field.planting_date,
    )

    price = field.expected_price_per_kg or 0.0
    variable_cost = field.variable_cost_per_ha or 0.0

    recommendations = decision_engine.generate_recommendations(
        agronomic_actions=agronomic_actions,
        yield_expected=prediction["yield_expected_kg_ha"],
        yield_p10=prediction["yield_p10_kg_ha"],
        yield_p90=prediction["yield_p90_kg_ha"],
        price_per_kg=price,
        variable_cost_per_ha=variable_cost,
        confidence=confidence_score,
        model_version=prediction["model_version"],
    )

    yield_gap = yield_gap_service.compute_yield_gap(
        crop=field.crop,
        predicted_yield_kg_ha=prediction["yield_expected_kg_ha"],
        features=features,
        water_balance=water_balance,
        phenology=phenology,
        regional_benchmark_kg_ha=_regional_benchmark(db, field),
    )

    feature_snapshot_id = str(uuid.uuid4())

    if persist:
        db.add(
            models.Prediction(
                field_id=field.id,
                model_id=prediction["model_id"],
                model_version=prediction["model_version"],
                feature_snapshot_id=feature_snapshot_id,
                yield_expected_kg_ha=prediction["yield_expected_kg_ha"],
                yield_p10_kg_ha=prediction["yield_p10_kg_ha"],
                yield_p50_kg_ha=prediction["yield_expected_kg_ha"],
                yield_p90_kg_ha=prediction["yield_p90_kg_ha"],
                confidence_score=confidence_score,
                confidence_tier=confidence_tier,
                risk_level=prediction["risk_level"],
                shap_explanation=prediction["shap_explanation"],
                feature_values=prediction["feature_values"],
            )
        )
        db.query(models.Recommendation).filter(
            models.Recommendation.field_id == field.id, models.Recommendation.status == "open"
        ).delete()
        for rec in recommendations:
            db.add(
                models.Recommendation(
                    field_id=field.id,
                    priority=rec["priority"],
                    issue=rec["issue"],
                    evidence=rec["evidence"],
                    suggested_action=rec["suggested_action"],
                    estimated_cost_per_ha=rec["estimated_cost_per_ha"],
                    expected_yield_delta_kg_ha=rec["expected_yield_delta_kg_ha"],
                    expected_margin_delta_per_ha=rec["expected_margin_delta_per_ha"],
                    expected_roi=rec["expected_roi"],
                    confidence=rec["confidence"],
                    decision=rec["decision"],
                    model_version=rec["model_version"],
                )
            )
        db.commit()

        profitability = compute_profitability(field, prediction)
        alert_engine.evaluate_alerts(db, field, features, prediction, profitability)

    return {
        "features": features,
        "prediction": prediction,
        "confidence_score": confidence_score,
        "confidence_tier": confidence_tier,
        "recommendations": recommendations,
        "phenology": phenology,
        "water_balance_summary": _water_balance_summary(water_balance),
        "yield_gap": yield_gap,
        "feature_snapshot_id": feature_snapshot_id,
    }


def _water_balance_summary(water_balance: dict) -> dict:
    if not water_balance.get("available"):
        return {"available": False}
    return {k: v for k, v in water_balance.items() if k != "series"}


def compute_profitability(field: models.Field, prediction: dict) -> dict:
    price = field.expected_price_per_kg or 0.0
    variable_cost = field.variable_cost_per_ha or 0.0
    yield_expected = prediction["yield_expected_kg_ha"]

    gross_revenue = economic_engine.gross_revenue_per_ha(yield_expected, price)
    margin = economic_engine.contribution_margin_per_ha(yield_expected, price, variable_cost)
    area = field.area_ha or 0.0

    downside_margin = economic_engine.contribution_margin_per_ha(prediction["yield_p10_kg_ha"], price, variable_cost)
    upside_margin = economic_engine.contribution_margin_per_ha(prediction["yield_p90_kg_ha"], price, variable_cost)

    return {
        "field_id": field.id,
        "yield_expected_kg_ha": yield_expected,
        "expected_price_per_kg": price,
        "gross_revenue_per_ha": gross_revenue,
        "variable_cost_per_ha": variable_cost,
        "contribution_margin_per_ha": margin,
        "total_area_ha": area,
        "total_expected_margin": round(margin * area, 2),
        "break_even_yield_kg_ha": economic_engine.break_even_yield(variable_cost, price),
        "break_even_price_per_kg": economic_engine.break_even_price(variable_cost, yield_expected),
        "downside_margin_per_ha": downside_margin,
        "upside_margin_per_ha": upside_margin,
    }
