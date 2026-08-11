"""SoilGrids / ISRIC — baseline fundamental de solo (spec 4.10).

API REST pública, sem autenticação: https://rest.isric.org/soilgrids/v2.0/docs
Cada profundidade é mantida separada — nunca fazemos média entre camadas
sem registrar a metodologia (spec 4.10).
"""
from __future__ import annotations

from app.providers.base import ProviderUnavailableError, SoilProvider
from app.providers.http_client import get_json

BASE_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

PROPERTIES = ["phh2o", "soc", "nitrogen", "clay", "sand", "silt", "cec", "bdod"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]

# SoilGrids returns most properties scaled by a conversion factor so values
# ship as integers. d_factor divides the raw "mean" value back to natural units.
CONVERSION_FACTOR = {
    "phh2o": 10,     # pH x 10
    "soc": 10,        # organic carbon, dg/kg -> g/kg
    "nitrogen": 100,  # cg/kg -> g/kg
    "clay": 10,       # g/kg -> %
    "sand": 10,
    "silt": 10,
    "cec": 10,        # mmol(c)/kg -> cmol(c)/kg
    "bdod": 100,      # cg/cm3 -> kg/dm3
}


class SoilGridsProvider(SoilProvider):
    name = "soilgrids"

    def properties(self, lat: float, lon: float) -> dict:
        params = [
            ("lon", lon),
            ("lat", lat),
            *[("property", p) for p in PROPERTIES],
            *[("depth", d) for d in DEPTHS],
            ("value", "mean"),
        ]
        data = get_json(BASE_URL, params=params)
        layers = data.get("properties", {}).get("layers", [])
        if not layers:
            raise ProviderUnavailableError("soilgrids: empty response payload")

        result: dict[str, dict[str, float]] = {d: {} for d in DEPTHS}
        for layer in layers:
            prop = layer.get("name")
            factor = CONVERSION_FACTOR.get(prop, 1)
            for depth_entry in layer.get("depths", []):
                depth_label = depth_entry.get("label")
                mean = depth_entry.get("values", {}).get("mean")
                if depth_label in result and mean is not None:
                    result[depth_label][prop] = round(mean / factor, 2)
        return {
            "source": self.name,
            "depths": result,
        }
