"""CHIRPS — precipitação histórica de alta resolução (spec 4.3, Fase 2).

CHIRPS é distribuído como rasters (GeoTIFF/NetCDF), não como uma API REST de
consulta por ponto sem autenticação. Formas de acesso: Google Earth Engine
(`UCSB-CHG/CHIRPS/DAILY`, requer ENABLE_EARTH_ENGINE + billing comercial) ou
download direto dos arquivos do Climate Hazards Center e extração por
pixel/zonal-stats no pipeline de ingestão (services/ingestion).

Implementação adiada para a Fase 2 (spec seção 60) — a interface abaixo já
reserva o contrato para não exigir refatoração do FeatureStore quando a
ingestão de rasters for implementada. Até lá, `rain_*` features usam a
série diária de precipitação do WeatherProvider histórico ativo (NASA POWER
ou INMET) — ver services/feature_engineering.py.
"""
from __future__ import annotations

from datetime import date

from app.providers.base import ProviderUnavailableError, WeatherProvider


class ChirpsProvider(WeatherProvider):
    name = "chirps"

    def historical(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        raise ProviderUnavailableError(
            "chirps: raster ingestion not implemented in MVP (Fase 2) — "
            "falling back to configured point-based historical provider"
        )
