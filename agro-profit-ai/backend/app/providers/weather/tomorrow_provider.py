"""Tomorrow.io — provider comercial opcional (spec 4.5/4.13).

Requer TOMORROW_API_KEY. O plano gratuito é voltado a desenvolvimento,
avaliação e baixo volume, sujeito a limites de uso.
"""
from __future__ import annotations

from datetime import date

from app.providers.base import ProviderUnavailableError, WeatherProvider
from app.providers.http_client import get_json

FORECAST_URL = "https://api.tomorrow.io/v4/weather/forecast"

FIELDS = [
    "temperatureMin",
    "temperatureMax",
    "temperatureAvg",
    "precipitationSum",
    "humidityAvg",
    "windSpeedAvg",
]


class TomorrowProvider(WeatherProvider):
    name = "tomorrow.io"

    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def forecast(self, lat: float, lon: float, days: int = 7) -> list[dict]:
        if not self.api_key:
            raise ProviderUnavailableError("tomorrow.io: TOMORROW_API_KEY not configured")
        data = get_json(FORECAST_URL, params={"location": f"{lat},{lon}", "apikey": self.api_key, "units": "metric"})
        rows = []
        for d in data.get("timelines", {}).get("daily", [])[:days]:
            values = d.get("values", {})
            rows.append(
                {
                    "date": d.get("time", "")[:10],
                    "kind": "forecast",
                    "provider": self.name,
                    "precipitation_mm": values.get("precipitationSum"),
                    "temperature_min_c": values.get("temperatureMin"),
                    "temperature_max_c": values.get("temperatureMax"),
                    "temperature_avg_c": values.get("temperatureAvg"),
                    "relative_humidity_pct": values.get("humidityAvg"),
                    "wind_speed_ms": values.get("windSpeedAvg"),
                }
            )
        return rows

    def historical(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        raise NotImplementedError("tomorrow.io: use NASA POWER / INMET for historical series")
