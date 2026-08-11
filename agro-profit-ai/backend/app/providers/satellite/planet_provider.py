"""Planet — conector opcional de avaliação, não fonte gratuita permanente
(spec 4.13). Requer PLANET_API_KEY de uma conta trial/paga; nunca usado
como caminho padrão do produto.
"""
from __future__ import annotations

from datetime import date

from app.config import settings
from app.providers.base import ProviderUnavailableError, SatelliteProvider

DATA_API_URL = "https://api.planet.com/data/v1"


class PlanetProvider(SatelliteProvider):
    name = "planet"

    def search_images(self, lat: float, lon: float, start: date, end: date, max_cloud_pct: float = 40.0) -> list[dict]:
        if not settings.PLANET_API_KEY:
            raise ProviderUnavailableError("planet: PLANET_API_KEY not configured (evaluation-only connector)")
        raise ProviderUnavailableError("planet: Data API search wiring not implemented in MVP")

    def vegetation_indices(self, lat: float, lon: float, target_date: date) -> dict:
        raise ProviderUnavailableError("planet: not implemented in MVP")
