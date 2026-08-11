"""Google Earth Engine — provider opcional, nunca obrigatório (spec 4.8).

Uso comercial do Earth Engine por empresas/startups exige configuração
comercial paga — por isso ENABLE_EARTH_ENGINE é false por padrão e nenhuma
regra de negócio depende deste provider.
"""
from __future__ import annotations

from datetime import date

from app.config import settings
from app.providers.base import ProviderUnavailableError, SatelliteProvider


class EarthEngineProvider(SatelliteProvider):
    name = "earth_engine"

    def _require_enabled(self):
        if not settings.ENABLE_EARTH_ENGINE:
            raise ProviderUnavailableError("earth_engine: disabled (ENABLE_EARTH_ENGINE=false)")

    def search_images(self, lat: float, lon: float, start: date, end: date, max_cloud_pct: float = 40.0) -> list[dict]:
        self._require_enabled()
        raise ProviderUnavailableError("earth_engine: ee.Initialize()/ImageCollection wiring not implemented in MVP")

    def vegetation_indices(self, lat: float, lon: float, target_date: date) -> dict:
        self._require_enabled()
        raise ProviderUnavailableError("earth_engine: not implemented in MVP")
