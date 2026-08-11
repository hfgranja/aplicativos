"""WeatherProviderRouter — cadeia de fallback (spec seção 52).

Histórico: INMET -> NASA POWER -> CHIRPS/ERA5 (Fase 2)
Previsão: provider comercial configurado pelo tenant -> Open-Meteo (se
ALLOW_NON_COMMERCIAL_PROVIDERS) -> vazio

Nunca deixa a indisponibilidade de um provider quebrar a requisição: cada
etapa é tentada e o router segue para a próxima em caso de
ProviderUnavailableError, registrando qual provider efetivamente respondeu.
"""
from __future__ import annotations

import logging
from datetime import date

from app.config import settings
from app.providers.base import ProviderUnavailableError
from app.providers.weather.chirps_provider import ChirpsProvider
from app.providers.weather.era5_provider import Era5Provider
from app.providers.weather.inmet_provider import InmetProvider
from app.providers.weather.nasa_power_provider import NasaPowerProvider
from app.providers.weather.openmeteo_provider import OpenMeteoProvider
from app.providers.weather.openweather_provider import OpenWeatherProvider
from app.providers.weather.tomorrow_provider import TomorrowProvider

logger = logging.getLogger("agroprofit.providers")


class WeatherProviderRouter:
    def __init__(self):
        self._historical_chain = [InmetProvider(), NasaPowerProvider(), ChirpsProvider(), Era5Provider()]
        self._forecast_chain = [
            OpenWeatherProvider(settings.OPENWEATHER_API_KEY),
            TomorrowProvider(settings.TOMORROW_API_KEY),
        ]
        if settings.ALLOW_NON_COMMERCIAL_PROVIDERS:
            self._forecast_chain.append(OpenMeteoProvider())

    def historical(self, lat: float, lon: float, start: date, end: date) -> tuple[list[dict], str]:
        for provider in self._historical_chain:
            try:
                rows = provider.historical(lat, lon, start, end)
                if rows:
                    return rows, provider.name
            except ProviderUnavailableError as exc:
                logger.info("historical weather fallback: %s unavailable (%s)", provider.name, exc)
                continue
        return [], "none"

    def forecast(self, lat: float, lon: float, days: int = 7) -> tuple[list[dict], str]:
        for provider in self._forecast_chain:
            try:
                rows = provider.forecast(lat, lon, days=days)
                if rows:
                    return rows, provider.name
            except (ProviderUnavailableError, NotImplementedError) as exc:
                logger.info("forecast fallback: %s unavailable (%s)", provider.name, exc)
                continue
        return [], "none"


weather_router = WeatherProviderRouter()
