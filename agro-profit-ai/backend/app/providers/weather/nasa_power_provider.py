"""NASA POWER — segunda fonte climática histórica e fallback (spec 4.2).

API pública, sem autenticação: https://power.larc.nasa.gov/docs/services/api/
"""
from __future__ import annotations

from datetime import date

from app.providers.base import ProviderUnavailableError, WeatherProvider
from app.providers.http_client import get_json

BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

PARAMETERS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS10M", "ALLSKY_SFC_SW_DWN", "PS"]


class NasaPowerProvider(WeatherProvider):
    name = "nasa_power"

    def historical(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        params = {
            "parameters": ",".join(PARAMETERS),
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
            "format": "JSON",
        }
        try:
            data = get_json(BASE_URL, params=params)
        except ProviderUnavailableError:
            raise
        parameters = data.get("properties", {}).get("parameter", {})
        if not parameters:
            raise ProviderUnavailableError("nasa_power: empty response payload")

        dates = sorted(parameters.get("T2M", {}).keys())
        observations = []
        for d in dates:
            def val(p: str) -> float | None:
                v = parameters.get(p, {}).get(d)
                # NASA POWER uses -999 as a fill value for missing data
                return None if v is None or v <= -900 else v

            observations.append(
                {
                    "date": f"{d[0:4]}-{d[4:6]}-{d[6:8]}",
                    "provider": self.name,
                    "precipitation_mm": val("PRECTOTCORR"),
                    "temperature_min_c": val("T2M_MIN"),
                    "temperature_max_c": val("T2M_MAX"),
                    "temperature_avg_c": val("T2M"),
                    "relative_humidity_pct": val("RH2M"),
                    "solar_radiation_mj_m2": (val("ALLSKY_SFC_SW_DWN") or 0) * 3.6 if val("ALLSKY_SFC_SW_DWN") is not None else None,
                    "wind_speed_ms": val("WS10M"),
                }
            )
        return observations
