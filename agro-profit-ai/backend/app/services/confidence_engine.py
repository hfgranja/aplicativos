"""Confidence Engine (spec seções 44-45).

Confidence is *computed*, not arbitrary: it aggregates data completeness,
satellite freshness, weather data quality/provenance, soil data quality,
and historical depth into a single 0-100 score, plus a cold-start tier.
"""
from __future__ import annotations

SYNTHETIC_PROVIDERS = {"synthetic_fallback"}


def _weather_quality(features: dict) -> float:
    if "_weather_provider" not in features:
        return 0.0
    provider = features["_weather_provider"]
    if provider in SYNTHETIC_PROVIDERS:
        return 0.15
    if provider == "inmet":
        return 1.0
    if provider == "nasa_power":
        return 0.85
    return 0.6


def _satellite_quality(features: dict) -> float:
    if "_satellite_scene_count" not in features:
        return 0.0
    if features.get("_satellite_is_synthetic"):
        return 0.2
    scene_count = features.get("_satellite_scene_count", 0)
    return min(1.0, 0.5 + scene_count / 20)


def _soil_quality(features: dict) -> float:
    source = features.get("_soil_source")
    if source is None:
        return 0.0
    if source == "laboratory":
        return 1.0
    if source == "soilgrids":
        return 0.65
    if source == "synthetic_fallback":
        return 0.1
    return 0.4


def _historical_quality(features: dict) -> float:
    n = features.get("historical_seasons_count") or 0
    return min(1.0, n / 4)


def compute_confidence(features: dict) -> tuple[float, str]:
    weights = {
        "weather": 0.25,
        "satellite": 0.25,
        "soil": 0.20,
        "historical": 0.30,
    }
    scores = {
        "weather": _weather_quality(features),
        "satellite": _satellite_quality(features),
        "soil": _soil_quality(features),
        "historical": _historical_quality(features),
    }
    score_0_1 = sum(weights[k] * scores[k] for k in weights)
    score_0_100 = round(score_0_1 * 100, 1)

    n_seasons = features.get("historical_seasons_count") or 0
    if n_seasons == 0:
        tier = "LOW"
    elif n_seasons == 1:
        tier = "MEDIUM"
    else:
        tier = "HIGHER"

    # A very low underlying data score caps the tier even with several
    # seasons on file (e.g. all-synthetic weather/soil).
    if score_0_100 < 35:
        tier = "LOW"
    elif score_0_100 < 65 and tier == "HIGHER":
        tier = "MEDIUM"

    return score_0_100, tier
