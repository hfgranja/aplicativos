"""INMET — clima observado no Brasil, fonte prioritária (spec 4.1).

Os dados meteorológicos coletados pelo INMET são públicos e de acesso
gratuito (estações automáticas, BDMEP). Este adapter usa a API pública
"apitempo" (https://apitempo.inmet.gov.br) para localizar a estação mais
próxima e ler o histórico diário. É uma API pública não versionada/sem SLA
formal — trate-a como best-effort e sempre com fallback para NASA POWER.

Nunca misturar observação de estação com previsão sem identificar a origem
(campo `provider` + `station_distance_km` persistidos em WeatherObservation).
"""
from __future__ import annotations

import math
from datetime import date
from functools import lru_cache

from app.providers.base import ProviderUnavailableError, WeatherProvider
from app.providers.http_client import get_json

BASE_URL = "https://apitempo.inmet.gov.br"


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class InmetProvider(WeatherProvider):
    name = "inmet"

    @lru_cache(maxsize=1)
    def get_stations(self) -> list[dict]:
        return get_json(f"{BASE_URL}/estacoes/T")

    def get_nearest_station(self, lat: float, lon: float) -> dict:
        stations = self.get_stations()
        if not stations:
            raise ProviderUnavailableError("inmet: no stations returned")
        best, best_dist = None, math.inf
        for s in stations:
            try:
                slat, slon = float(s["VL_LATITUDE"]), float(s["VL_LONGITUDE"])
            except (KeyError, TypeError, ValueError):
                continue
            dist = _haversine_km(lat, lon, slat, slon)
            if dist < best_dist:
                best, best_dist = s, dist
        if best is None:
            raise ProviderUnavailableError("inmet: could not resolve nearest station")
        best = {**best, "distance_km": round(best_dist, 1)}
        return best

    def get_daily_history(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        station = self.get_nearest_station(lat, lon)
        code = station.get("CD_ESTACAO")
        raw = get_json(f"{BASE_URL}/estacao/diaria/{start.isoformat()}/{end.isoformat()}/{code}")
        rows = []
        for r in raw:
            rows.append(
                {
                    "date": r.get("DT_MEDICAO"),
                    "provider": self.name,
                    "station_distance_km": station["distance_km"],
                    "precipitation_mm": _num(r.get("CHUVA")),
                    "temperature_min_c": _num(r.get("TEMP_MIN")),
                    "temperature_max_c": _num(r.get("TEMP_MAX")),
                    "temperature_avg_c": _num(r.get("TEMP_MED")),
                    "relative_humidity_pct": _num(r.get("UMID_MED")),
                    "solar_radiation_mj_m2": _num(r.get("RADIACAO")),
                    "wind_speed_ms": _num(r.get("VEL_VENTO_MED")),
                }
            )
        return rows

    def get_hourly_history(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        station = self.get_nearest_station(lat, lon)
        code = station.get("CD_ESTACAO")
        raw = get_json(f"{BASE_URL}/estacao/{start.isoformat()}/{end.isoformat()}/{code}")
        return raw

    def historical(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        return self.get_daily_history(lat, lon, start, end)


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None
