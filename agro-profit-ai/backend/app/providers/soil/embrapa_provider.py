"""Embrapa GeoInfo — fonte pública brasileira complementar (spec 4.11).

O GeoInfo publica datasets heterogêneos (WMS, WFS, GeoTIFF, Shapefile) por
catálogo próprio, cada um com schema diferente — não há um endpoint único de
consulta por ponto. A ingestão real acontece via importação manual de
dataset (ver Farm Data Hub / futuro Soil Laboratory Importer), não por
chamada síncrona neste provider.
"""
from __future__ import annotations

from app.providers.base import ProviderUnavailableError, SoilProvider


class EmbrapaProvider(SoilProvider):
    name = "embrapa_geoinfo"

    def properties(self, lat: float, lon: float) -> dict:
        raise ProviderUnavailableError(
            "embrapa_geoinfo: requires per-dataset WMS/WFS/GeoTIFF import — not a point-query API"
        )
