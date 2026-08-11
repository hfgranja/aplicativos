"""Open-Meteo — previsão gratuita para desenvolvimento não comercial (spec 4.5).

O serviço público gratuito é destinado a uso não comercial. Uma implantação
comercial deve contratar o Open-Meteo API (customer plan) ou fazer self-host
do modelo. Por isso este provider só é habilitado quando
ALLOW_NON_COMMERCIAL_PROVIDERS=true (ver app/config.py).
"""
from __future__ import annotations

from datetime import date

from app.providers.base import ProviderUnavailableError, WeatherProvider
from app.providers.http_client import get_json

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "shortwave_radiation_sum",
    "wind_speed_10m_max",
]


class OpenMeteoProvider(WeatherProvider):
    name = "open-meteo"

    def historical(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": ",".join(DAILY_VARS),
            "timezone": "auto",
        }
        data = get_json(ARCHIVE_URL, params=params)
        return self._parse_daily(data)

    def forecast(self, lat: float, lon: float, days: int = 7) -> list[dict]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "forecast_days": min(days, 16),
            "daily": ",".join(DAILY_VARS),
            "timezone": "auto",
        }
        data = get_json(FORECAST_URL, params=params)
        return self._parse_daily(data, kind="forecast")

    @staticmethod
    def _parse_daily(data: dict, kind: str = "observation") -> list[dict]:
        daily = data.get("daily")
        if not daily or "time" not in daily:
            raise ProviderUnavailableError("open-meteo: empty response payload")
        rows = []
        for i, d in enumerate(daily["time"]):
            rows.append(
                {
                    "date": d,
                    "kind": kind,
                    "provider": "open-meteo",
                    "precipitation_mm": _at(daily, "precipitation_sum", i),
                    "temperature_min_c": _at(daily, "temperature_2m_min", i),
                    "temperature_max_c": _at(daily, "temperature_2m_max", i),
                    "temperature_avg_c": _at(daily, "temperature_2m_mean", i),
                    "relative_humidity_pct": _at(daily, "relative_humidity_2m_mean", i),
                    "solar_radiation_mj_m2": _at(daily, "shortwave_radiation_sum", i),
                    "wind_speed_ms": _kmh_to_ms(_at(daily, "wind_speed_10m_max", i)),
                }
            )
        return rows


def _at(daily: dict, key: str, i: int):
    values = daily.get(key)
    if not values or i >= len(values):
        return None
    return values[i]


def _kmh_to_ms(v):
    return None if v is None else round(v / 3.6, 2)
