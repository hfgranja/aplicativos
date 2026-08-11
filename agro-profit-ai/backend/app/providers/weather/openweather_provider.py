"""OpenWeather — provider comercial opcional (spec 4.5/4.13).

Requer OPENWEATHER_API_KEY. Franquia gratuita limitada conforme plano
vigente na OpenWeather — verificar em runtime, não assumir volume fixo.
"""
from __future__ import annotations

from datetime import date

from app.providers.base import ProviderUnavailableError, WeatherProvider
from app.providers.http_client import get_json

ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"


class OpenWeatherProvider(WeatherProvider):
    name = "openweather"

    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def _require_key(self):
        if not self.api_key:
            raise ProviderUnavailableError("openweather: OPENWEATHER_API_KEY not configured")

    def forecast(self, lat: float, lon: float, days: int = 7) -> list[dict]:
        self._require_key()
        data = get_json(
            ONECALL_URL,
            params={
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
                "exclude": "minutely,hourly,alerts,current",
            },
        )
        rows = []
        for d in data.get("daily", [])[:days]:
            temp = d.get("temp", {})
            rows.append(
                {
                    "date": date.fromtimestamp(d["dt"]).isoformat(),
                    "kind": "forecast",
                    "provider": self.name,
                    "precipitation_mm": (d.get("rain") or 0) if isinstance(d.get("rain"), (int, float)) else 0,
                    "temperature_min_c": temp.get("min"),
                    "temperature_max_c": temp.get("max"),
                    "temperature_avg_c": temp.get("day"),
                    "relative_humidity_pct": d.get("humidity"),
                    "wind_speed_ms": d.get("wind_speed"),
                }
            )
        return rows

    def historical(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        raise NotImplementedError("openweather: use NASA POWER / INMET for historical series")

    def current(self, lat: float, lon: float) -> dict:
        self._require_key()
        data = get_json(
            ONECALL_URL,
            params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric", "exclude": "minutely,hourly,daily,alerts"},
        )
        cur = data.get("current", {})
        return {
            "provider": self.name,
            "temperature_avg_c": cur.get("temp"),
            "relative_humidity_pct": cur.get("humidity"),
            "wind_speed_ms": cur.get("wind_speed"),
        }
