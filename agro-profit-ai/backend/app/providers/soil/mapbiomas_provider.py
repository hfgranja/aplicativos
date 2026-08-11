"""MapBiomas — cobertura/uso da terra + solo contextual (spec 4.9).

MapBiomas distribui seus produtos como coleções raster no Google Earth
Engine e via downloads em massa — não há endpoint REST público de consulta
por ponto sem processamento próprio. Este adapter documenta o contrato e
fica desabilitado até a ingestão via Earth Engine (ENABLE_EARTH_ENGINE) ou
download+zonal-stats ser implementada (Fase 2, spec seção 60).

Usar sempre como camada contextual — nunca substituir análise laboratorial
de solo por valores do MapBiomas (spec 4.9).
"""
from __future__ import annotations

from app.providers.base import ProviderUnavailableError, SoilProvider


class MapBiomasProvider(SoilProvider):
    name = "mapbiomas"

    def properties(self, lat: float, lon: float) -> dict:
        raise ProviderUnavailableError("mapbiomas: point-query ingestion not implemented in MVP (Fase 2)")

    def land_cover(self, lat: float, lon: float, year: int) -> dict:
        raise ProviderUnavailableError("mapbiomas: land cover ingestion not implemented in MVP (Fase 2)")
