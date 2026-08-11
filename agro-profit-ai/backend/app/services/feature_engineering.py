"""Feature Store — Gold layer (spec seções 11-15).

Reads already-ingested Bronze/Silver rows (WeatherObservation,
SatelliteObservation, SoilSample) and derives the feature vector consumed
by the ML models and the Decision Engine. Never calls providers directly.
"""
from __future__ import annotations

import statistics
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app import models

RAIN_WINDOWS = (1, 3, 7, 15, 30, 60, 90)
BASE_TEMPERATURE_C = 10.0  # GDD base temperature, generic row crop


def _rain_sum(obs: list[models.WeatherObservation], days: int, as_of: datetime) -> float:
    cutoff = as_of - timedelta(days=days)
    return round(sum(o.precipitation_mm or 0.0 for o in obs if cutoff <= o.date <= as_of), 1)


def _consecutive_dry_days(obs: list[models.WeatherObservation], as_of: datetime) -> int:
    ordered = sorted([o for o in obs if o.date <= as_of], key=lambda o: o.date, reverse=True)
    streak = 0
    for o in ordered:
        if (o.precipitation_mm or 0.0) < 1.0:
            streak += 1
        else:
            break
    return streak


def build_weather_features(db: Session, field: models.Field) -> dict:
    as_of = datetime.utcnow()
    obs = (
        db.query(models.WeatherObservation)
        .filter(models.WeatherObservation.field_id == field.id, models.WeatherObservation.kind == "observation")
        .order_by(models.WeatherObservation.date)
        .all()
    )
    if not obs:
        return {}

    features: dict = {}
    for w in RAIN_WINDOWS:
        features[f"rain_{w}d"] = _rain_sum(obs, w, as_of)

    last_30 = [o for o in obs if o.date >= as_of - timedelta(days=30)]
    last_90 = [o for o in obs if o.date >= as_of - timedelta(days=90)]

    def avg(values):
        vals = [v for v in values if v is not None]
        return round(statistics.fmean(vals), 2) if vals else None

    features["temperature_mean_30d"] = avg([o.temperature_avg_c for o in last_30])
    features["temperature_min_30d"] = avg([o.temperature_min_c for o in last_30])
    features["temperature_max_30d"] = avg([o.temperature_max_c for o in last_30])
    features["relative_humidity_30d"] = avg([o.relative_humidity_pct for o in last_30])
    features["solar_radiation_30d"] = round(sum(o.solar_radiation_mj_m2 or 0.0 for o in last_30), 1)
    features["growing_degree_days_90d"] = round(
        sum(max(0.0, (o.temperature_avg_c or BASE_TEMPERATURE_C) - BASE_TEMPERATURE_C) for o in last_90), 1
    )
    features["consecutive_dry_days"] = _consecutive_dry_days(obs, as_of)
    features["heat_stress_days_30d"] = sum(1 for o in last_30 if (o.temperature_max_c or 0) > 34)
    # Simple water balance proxy: precipitation minus a fixed reference ET (mm/day ~4.5)
    features["water_balance_30d"] = round(features["rain_30d"] - 4.5 * 30, 1)
    features["_weather_provider"] = obs[-1].provider
    features["_weather_last_date"] = obs[-1].date.isoformat()
    return features


def build_satellite_features(db: Session, field: models.Field) -> dict:
    as_of = datetime.utcnow()
    obs = (
        db.query(models.SatelliteObservation)
        .filter(models.SatelliteObservation.field_id == field.id)
        .order_by(models.SatelliteObservation.date)
        .all()
    )
    if not obs:
        return {}

    def series(attr):
        return [getattr(o, attr) for o in obs if getattr(o, attr) is not None]

    last_30 = [o for o in obs if o.date >= as_of - timedelta(days=30)]
    ndvi_series = series("ndvi")
    features = {
        "ndvi_current": obs[-1].ndvi,
        "ndvi_mean_30d": round(statistics.fmean([o.ndvi for o in last_30 if o.ndvi is not None]), 3) if last_30 else None,
        "ndvi_std_30d": round(statistics.pstdev([o.ndvi for o in last_30 if o.ndvi is not None]), 3) if len(last_30) > 1 else 0.0,
        "ndre_current": obs[-1].ndre,
        "ndmi_current": obs[-1].ndmi,
        "evi_current": obs[-1].evi,
        "ndvi_trend": round(ndvi_series[-1] - ndvi_series[0], 3) if len(ndvi_series) > 1 else 0.0,
        "_satellite_is_synthetic": obs[-1].is_synthetic,
        "_satellite_last_date": obs[-1].date.isoformat(),
        "_satellite_scene_count": len(obs),
    }
    return features


def build_soil_features(db: Session, field: models.Field) -> dict:
    sample = (
        db.query(models.SoilSample)
        .filter(models.SoilSample.field_id == field.id)
        .order_by(models.SoilSample.sample_date.desc())
        .first()
    )
    if not sample:
        return {}
    return {
        "soil_ph": sample.ph,
        "soil_organic_matter": sample.organic_matter,
        "soil_clay": sample.clay,
        "soil_sand": sample.sand,
        "soil_silt": sample.silt,
        "soil_cec": sample.cec,
        "soil_base_saturation": sample.base_saturation,
        "soil_phosphorus": sample.phosphorus,
        "soil_potassium": sample.potassium,
        "_soil_source": sample.source,
        "_soil_sample_date": sample.sample_date.isoformat() if sample.sample_date else None,
    }


def build_management_features(db: Session, field: models.Field) -> dict:
    ops = db.query(models.Operation).filter(models.Operation.field_id == field.id, models.Operation.season == field.season).all()
    fert_cost = sum(o.cost_per_ha or 0 for o in ops if o.operation_type == "fertilization")
    defensive_cost = sum(o.cost_per_ha or 0 for o in ops if o.operation_type == "defensive")
    irrigation_events = sum(1 for o in ops if o.operation_type == "irrigation")
    return {
        "fertilizer_cost_per_ha": round(fert_cost, 2),
        "defensive_cost_per_ha": round(defensive_cost, 2),
        "irrigation_events": irrigation_events,
        "operations_count": len(ops),
    }


def build_historical_features(db: Session, field: models.Field) -> dict:
    records = db.query(models.YieldRecord).filter(models.YieldRecord.field_id == field.id).all()
    yields = [r.yield_kg_ha for r in records]
    return {
        "historical_seasons_count": len(records),
        "historical_yield_mean_kg_ha": round(statistics.fmean(yields), 1) if yields else None,
        "historical_yield_std_kg_ha": round(statistics.pstdev(yields), 1) if len(yields) > 1 else None,
    }


def build_field_features(db: Session, field: models.Field) -> dict:
    """Assembles the full Gold-layer feature vector for a field, as of now."""
    features: dict = {"crop": field.crop, "area_ha": field.area_ha}
    features.update(build_weather_features(db, field))
    features.update(build_satellite_features(db, field))
    features.update(build_soil_features(db, field))
    features.update(build_management_features(db, field))
    features.update(build_historical_features(db, field))
    return features
