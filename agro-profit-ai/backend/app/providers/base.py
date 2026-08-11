"""Provider interfaces (spec seção 3).

Nenhum fornecedor externo deve ficar acoplado às regras de negócio: toda
integração passa por uma destas interfaces, para que trocar de fonte não
exija reescrever services/ml/routers. Cada implementação concreta deve ser
resiliente (timeout curto + fallback) — nunca deixar a indisponibilidade de
um provider derrubar a aplicação (spec seção 51).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Optional


class ProviderUnavailableError(Exception):
    """Raised by an adapter when the upstream source could not be reached
    or returned no usable data. Callers (ProviderRouter) catch this to
    fall through to the next provider in the chain."""


class WeatherProvider(ABC):
    name: str = "base"
    kind: str = "weather"

    @abstractmethod
    def historical(self, lat: float, lon: float, start: date, end: date) -> list[dict[str, Any]]:
        """Daily observations: precipitation_mm, temperature_min/max/avg_c,
        relative_humidity_pct, solar_radiation_mj_m2, wind_speed_ms."""

    def forecast(self, lat: float, lon: float, days: int = 7) -> list[dict[str, Any]]:
        raise NotImplementedError(f"{self.name} does not implement forecast()")

    def current(self, lat: float, lon: float) -> Optional[dict[str, Any]]:
        raise NotImplementedError(f"{self.name} does not implement current()")


class SatelliteProvider(ABC):
    name: str = "base"

    @abstractmethod
    def search_images(self, lat: float, lon: float, start: date, end: date, max_cloud_pct: float = 40.0) -> list[dict]:
        """Returns available scene metadata (date, cloud_cover_pct, product_id)."""

    @abstractmethod
    def vegetation_indices(self, lat: float, lon: float, target_date: date) -> Optional[dict[str, float]]:
        """Returns {ndvi, ndre, evi, savi, gndvi, ndmi, ndwi, bsi} for the pixel/cell nearest target_date."""


class SoilProvider(ABC):
    name: str = "base"

    @abstractmethod
    def properties(self, lat: float, lon: float) -> Optional[dict[str, Any]]:
        """Returns baseline soil properties by depth interval, e.g.
        {"0-5cm": {"ph": 5.4, "clay": 32, ...}, "5-15cm": {...}}."""


class MarketPriceProvider(ABC):
    name: str = "base"

    @abstractmethod
    def historical_prices(self, crop: str, start: date, end: date) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def current_price(self, crop: str) -> Optional[float]:
        ...


class FarmDataProvider(ABC):
    """Internal provider — reads producer-uploaded data from our own DB
    (spec section 4: FarmDataProvider.operations / yield_history)."""

    @abstractmethod
    def operations(self, field_id: str, season: Optional[str] = None) -> list[dict]:
        ...

    @abstractmethod
    def yield_history(self, field_id: str) -> list[dict]:
        ...


class RegionalBenchmarkProvider(ABC):
    name: str = "base"

    @abstractmethod
    def municipal_yield(self, crop: str, ibge_municipality_code: str, year: int) -> Optional[dict[str, Any]]:
        """Regional benchmark — never used as ground truth for a field, only
        as cold-start prior / anomaly baseline (spec section 4.12)."""
