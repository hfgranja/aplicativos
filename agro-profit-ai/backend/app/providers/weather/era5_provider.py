"""ERA5-Land — reanálise histórica horária desde 1950 (spec 4.4, Fase 2).

Acesso via Copernicus Climate Data Store (CDS) API, que exige credenciais
próprias (CDS_API_KEY) e opera por submissão assíncrona de job + polling
(pacote `cdsapi`), incompatível com uma chamada HTTP síncrona simples.

Reservado para a Fase 2 (spec seção 60): a ingestão de ERA5-Land deve rodar
como job batch em services/ingestion (ver app/routers/... scheduler),
persistindo os resultados em WeatherObservation com provider="era5", não
como chamada síncrona por requisição de usuário.
"""
from __future__ import annotations

from datetime import date

from app.config import settings
from app.providers.base import ProviderUnavailableError, WeatherProvider


class Era5Provider(WeatherProvider):
    name = "era5"

    def historical(self, lat: float, lon: float, start: date, end: date) -> list[dict]:
        if not settings.CDS_API_KEY:
            raise ProviderUnavailableError("era5: CDS_API_KEY not configured (Fase 2 — batch ingestion only)")
        raise ProviderUnavailableError("era5: batch ingestion job not implemented in this MVP")
