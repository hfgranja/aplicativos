"""Ingestion layer — pulls from provider adapters into the Bronze/Silver
tables (WeatherObservation, SatelliteObservation, SoilSample), idempotently.

Feature engineering (services/feature_engineering.py) never calls providers
directly — it only reads already-ingested rows. This keeps the ML/decision
path fast, cacheable, and independent of upstream provider availability
(spec seções 10-11, 53: "o sistema deverá privilegiar cache antes de nova
chamada").

When every real provider in the chain is unavailable (no credentials, no
network — e.g. offline dev), a clearly-labeled synthetic fallback is
persisted instead of leaving the pipeline empty, so the rest of the product
(features, ML, decision engine, UI) stays exercisable end-to-end. Synthetic
rows are never presented to the user as real observations — see
provider="synthetic_fallback" / is_synthetic=True and Confidence Engine
scoring in services/confidence_engine.py.
"""
from __future__ import annotations

import hashlib
import math
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app import models
from app.providers.satellite.copernicus_provider import CopernicusProvider
from app.providers.soil.soilgrids_provider import SoilGridsProvider
from app.providers.base import ProviderUnavailableError
from app.providers.weather.router import weather_router

_satellite_provider = CopernicusProvider()
_soil_provider = SoilGridsProvider()


def _synthetic_weather_row(lat: float, lon: float, d: date) -> dict:
    seed = f"{round(lat, 3)}:{round(lon, 3)}:{d.isoformat()}"
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    jitter = (h % 1000) / 1000.0
    doy = d.timetuple().tm_yday
    seasonal_temp = 24 + 6 * math.sin(2 * math.pi * (doy - 30) / 365.0)
    rain_prob = 0.35 + 0.25 * math.sin(2 * math.pi * (doy - 300) / 365.0)
    precip = round(max(0.0, (jitter - (1 - rain_prob)) * 45), 1) if jitter > (1 - rain_prob) else 0.0
    return {
        "date": d.isoformat(),
        "kind": "observation",
        "provider": "synthetic_fallback",
        "precipitation_mm": precip,
        "temperature_min_c": round(seasonal_temp - 6 + jitter, 1),
        "temperature_max_c": round(seasonal_temp + 6 + jitter, 1),
        "temperature_avg_c": round(seasonal_temp + jitter - 0.5, 1),
        "relative_humidity_pct": round(55 + 20 * jitter, 1),
        "solar_radiation_mj_m2": round(18 + 4 * jitter, 1),
        "wind_speed_ms": round(1.5 + 2 * jitter, 1),
    }


def ensure_weather_ingested(db: Session, field: models.Field, days_back: int = 120) -> str:
    """Returns the provider name that ended up populating the window."""
    end = datetime.utcnow().date()
    start = end - timedelta(days=days_back)

    existing_dates = {
        o.date.date()
        for o in db.query(models.WeatherObservation)
        .filter(models.WeatherObservation.field_id == field.id, models.WeatherObservation.kind == "observation")
        .filter(models.WeatherObservation.date >= datetime.combine(start, datetime.min.time()))
        .all()
    }
    missing_days = (end - start).days + 1
    if len(existing_dates) >= missing_days * 0.8:
        # Already have a near-complete window cached — skip re-fetching.
        latest = (
            db.query(models.WeatherObservation)
            .filter(models.WeatherObservation.field_id == field.id)
            .order_by(models.WeatherObservation.date.desc())
            .first()
        )
        return latest.provider if latest else "none"

    rows, provider_name = weather_router.historical(field.centroid_lat, field.centroid_lon, start, end)
    used_synthetic = False
    if not rows:
        used_synthetic = True
        d = start
        rows = []
        while d <= end:
            rows.append(_synthetic_weather_row(field.centroid_lat, field.centroid_lon, d))
            d += timedelta(days=1)
        provider_name = "synthetic_fallback"

    inserted = 0
    for r in rows:
        row_date = datetime.fromisoformat(r["date"]) if isinstance(r["date"], str) else r["date"]
        if row_date.date() in existing_dates:
            continue
        db.add(
            models.WeatherObservation(
                field_id=field.id,
                date=row_date,
                kind=r.get("kind", "observation"),
                provider=r.get("provider", provider_name),
                station_distance_km=r.get("station_distance_km"),
                precipitation_mm=r.get("precipitation_mm"),
                temperature_min_c=r.get("temperature_min_c"),
                temperature_max_c=r.get("temperature_max_c"),
                temperature_avg_c=r.get("temperature_avg_c"),
                relative_humidity_pct=r.get("relative_humidity_pct"),
                solar_radiation_mj_m2=r.get("solar_radiation_mj_m2"),
                wind_speed_ms=r.get("wind_speed_ms"),
            )
        )
        inserted += 1
    if inserted:
        db.commit()
    return "synthetic_fallback" if used_synthetic else provider_name


def ensure_forecast_ingested(db: Session, field: models.Field, days: int = 7) -> list[dict]:
    """Ingere previsão dos próximos dias (kind='forecast') via cadeia de
    providers de forecast; retorna as linhas (novas + cacheadas de hoje).
    Previsões velhas são substituídas — nunca misturadas com observação
    (spec 4.1: origem sempre identificada)."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    cached = (
        db.query(models.WeatherObservation)
        .filter(
            models.WeatherObservation.field_id == field.id,
            models.WeatherObservation.kind == "forecast",
            models.WeatherObservation.created_at >= today,
        )
        .order_by(models.WeatherObservation.date)
        .all()
    )
    if cached:
        return [
            {
                "date": c.date.date().isoformat(),
                "precipitation_mm": c.precipitation_mm,
                "temperature_min_c": c.temperature_min_c,
                "temperature_max_c": c.temperature_max_c,
                "provider": c.provider,
            }
            for c in cached
        ]

    rows, provider_name = weather_router.forecast(field.centroid_lat, field.centroid_lon, days=days)
    if not rows:
        return []

    # descarta previsões de execuções anteriores antes de gravar as novas
    db.query(models.WeatherObservation).filter(
        models.WeatherObservation.field_id == field.id,
        models.WeatherObservation.kind == "forecast",
    ).delete()
    for r in rows:
        row_date = datetime.fromisoformat(r["date"]) if isinstance(r["date"], str) else r["date"]
        db.add(
            models.WeatherObservation(
                field_id=field.id,
                date=row_date,
                kind="forecast",
                provider=r.get("provider", provider_name),
                precipitation_mm=r.get("precipitation_mm"),
                temperature_min_c=r.get("temperature_min_c"),
                temperature_max_c=r.get("temperature_max_c"),
                temperature_avg_c=r.get("temperature_avg_c"),
                relative_humidity_pct=r.get("relative_humidity_pct"),
                wind_speed_ms=r.get("wind_speed_ms"),
            )
        )
    db.commit()
    return rows


def ensure_satellite_ingested(db: Session, field: models.Field, days_back: int = 60) -> None:
    existing = (
        db.query(models.SatelliteObservation)
        .filter(models.SatelliteObservation.field_id == field.id)
        .order_by(models.SatelliteObservation.date.desc())
        .first()
    )
    if existing and existing.date.date() >= date.today() - timedelta(days=5):
        return

    end = date.today()
    start = end - timedelta(days=days_back)
    scenes = _satellite_provider.search_images(field.centroid_lat, field.centroid_lon, start, end)
    for scene in scenes:
        scene_date = datetime.fromisoformat(scene["date"]).date() if isinstance(scene["date"], str) else scene["date"]
        already = (
            db.query(models.SatelliteObservation)
            .filter(models.SatelliteObservation.field_id == field.id)
            .filter(models.SatelliteObservation.date == datetime.combine(scene_date, datetime.min.time()))
            .first()
        )
        if already:
            continue
        try:
            indices = _satellite_provider.vegetation_indices(field.centroid_lat, field.centroid_lon, scene_date)
        except ProviderUnavailableError:
            continue
        db.add(
            models.SatelliteObservation(
                field_id=field.id,
                date=datetime.combine(scene_date, datetime.min.time()),
                provider=_satellite_provider.name,
                cloud_cover_pct=scene.get("cloud_cover_pct"),
                ndvi=indices.get("ndvi"),
                ndre=indices.get("ndre"),
                evi=indices.get("evi"),
                savi=indices.get("savi"),
                gndvi=indices.get("gndvi"),
                ndmi=indices.get("ndmi"),
                ndwi=indices.get("ndwi"),
                bsi=indices.get("bsi"),
                is_synthetic=bool(indices.get("is_synthetic", scene.get("is_synthetic", False))),
            )
        )
    db.commit()


def ensure_soil_ingested(db: Session, field: models.Field) -> None:
    existing = db.query(models.SoilSample).filter(models.SoilSample.field_id == field.id).first()
    if existing:
        return
    try:
        result = _soil_provider.properties(field.centroid_lat, field.centroid_lon)
        topsoil = result["depths"].get("0-5cm", {})
        subsoil = result["depths"].get("5-15cm", {})
        db.add(
            models.SoilSample(
                field_id=field.id,
                sample_id="soilgrids-auto",
                latitude=field.centroid_lat,
                longitude=field.centroid_lon,
                sample_date=datetime.utcnow(),
                depth_cm="0-15",
                ph=topsoil.get("phh2o"),
                organic_matter=topsoil.get("soc"),
                clay=topsoil.get("clay"),
                sand=topsoil.get("sand"),
                silt=topsoil.get("silt"),
                cec=topsoil.get("cec") or subsoil.get("cec"),
                source="soilgrids",
            )
        )
        db.commit()
    except ProviderUnavailableError:
        # No lab sample and SoilGrids unreachable — regional defaults for a
        # generic Brazilian Cerrado oxisol, clearly tagged as synthetic so
        # the confidence engine penalizes it heavily.
        db.add(
            models.SoilSample(
                field_id=field.id,
                sample_id="regional-default",
                latitude=field.centroid_lat,
                longitude=field.centroid_lon,
                sample_date=datetime.utcnow(),
                depth_cm="0-20",
                ph=5.4,
                organic_matter=22.0,
                clay=35.0,
                sand=40.0,
                silt=25.0,
                cec=8.5,
                source="synthetic_fallback",
            )
        )
        db.commit()


def ensure_field_data_ingested(db: Session, field: models.Field) -> dict[str, str]:
    weather_provider = ensure_weather_ingested(db, field)
    ensure_satellite_ingested(db, field)
    ensure_soil_ingested(db, field)
    ensure_forecast_ingested(db, field)
    return {"weather_provider": weather_provider}
