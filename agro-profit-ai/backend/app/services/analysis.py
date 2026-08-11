"""Orchestrates the full pipeline for a field (spec seção 70):

DATA -> INGESTION -> FEATURE STORE -> ML PREDICTION -> RISK -> ECONOMIC
-> DECISION -> RECOMMENDATION -> EXPLANATION

Routers call this instead of touching providers/ml/services directly, so
every read endpoint (analysis, yield-forecast, profitability,
recommendations) stays consistent.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import models
from app.ml.yield_model import predict_yield
from app.services import alert_engine, confidence_engine, decision_engine, economic_engine, feature_engineering, ingestion


def run_field_analysis(db: Session, field: models.Field, persist: bool = True) -> dict:
    ingestion.ensure_field_data_ingested(db, field)
    features = feature_engineering.build_field_features(db, field)

    prediction = predict_yield(field.crop, features)
    confidence_score, confidence_tier = confidence_engine.compute_confidence(features)

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
        db.commit()

    price = field.expected_price_per_kg or 0.0
    variable_cost = field.variable_cost_per_ha or 0.0

    recommendations = decision_engine.generate_recommendations(
        features=features,
        yield_expected=prediction["yield_expected_kg_ha"],
        yield_p10=prediction["yield_p10_kg_ha"],
        yield_p90=prediction["yield_p90_kg_ha"],
        price_per_kg=price,
        variable_cost_per_ha=variable_cost,
        confidence=confidence_score,
        model_version=prediction["model_version"],
    )

    if persist:
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
        "feature_snapshot_id": feature_snapshot_id,
    }


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
