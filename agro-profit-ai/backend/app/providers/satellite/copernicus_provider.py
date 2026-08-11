"""Copernicus Data Space Ecosystem / Sentinel Hub — fonte orbital principal
(spec 4.6-4.7).

Produtos Sentinel-2 L2A são gratuitos, inclusive para uso comercial. O
acesso real usa OAuth2 client-credentials (COPERNICUS_CLIENT_ID/SECRET)
contra o Catalog API (busca de cenas) e o Statistical/Process API (cálculo
de índices por geometria). Sem credenciais configuradas — como neste
ambiente de desenvolvimento — o adapter cai em um gerador sintético
determinístico (seed = lat/lon/data) para que o restante do pipeline
(feature store, ML, UI) seja exercitável ponta a ponta; toda observação
sintética é marcada `is_synthetic=True` e NUNCA deve ser exibida como
imagem real ao usuário (spec 4.6: nunca recalcular/confundir fonte).
"""
from __future__ import annotations

import hashlib
import math
from datetime import date, timedelta

from app.config import settings
from app.providers.base import ProviderUnavailableError, SatelliteProvider
from app.providers.http_client import DEFAULT_TIMEOUT

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/stac"
STATISTICS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"

BANDS = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]


def _has_credentials() -> bool:
    return bool(settings.COPERNICUS_CLIENT_ID and settings.COPERNICUS_CLIENT_SECRET)


def _synthetic_indices(lat: float, lon: float, target_date: date) -> dict[str, float]:
    """Deterministic pseudo-NDVI-family series for dev/demo. Seasonal curve
    (Southern Hemisphere crop cycle) + spatial + per-date jitter, clamped to
    physically plausible index ranges."""
    seed = f"{round(lat, 4)}:{round(lon, 4)}:{target_date.isoformat()}"
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    jitter = ((h % 2000) / 1000.0 - 1.0) * 0.05  # +-0.05

    day_of_year = target_date.timetuple().tm_yday
    # peak greenness around day ~290 (Oct planting -> Jan/Feb peak in BR), trough at ~150
    phase = math.cos(2 * math.pi * (day_of_year - 40) / 365.0)
    ndvi = max(0.15, min(0.92, 0.55 + 0.30 * phase + jitter))

    return {
        "ndvi": round(ndvi, 3),
        "ndre": round(max(0.05, ndvi * 0.55 + jitter * 0.3), 3),
        "evi": round(max(0.05, ndvi * 0.85 + jitter * 0.2), 3),
        "savi": round(max(0.05, ndvi * 0.80 + jitter * 0.2), 3),
        "gndvi": round(max(0.05, ndvi * 0.90 + jitter * 0.2), 3),
        "ndmi": round(max(-0.2, ndvi * 0.60 - 0.05 + jitter * 0.3), 3),
        "ndwi": round(max(-0.5, ndvi * 0.30 - 0.35 + jitter * 0.2), 3),
        "bsi": round(max(-0.5, 0.30 - ndvi * 0.45 + jitter * 0.2), 3),
    }


class CopernicusProvider(SatelliteProvider):
    name = "copernicus_sentinel2"

    def __init__(self):
        self._token: str | None = None

    def _get_token(self) -> str:
        if not _has_credentials():
            raise ProviderUnavailableError("copernicus: COPERNICUS_CLIENT_ID/SECRET not configured")
        import httpx

        resp = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.COPERNICUS_CLIENT_ID,
                "client_secret": settings.COPERNICUS_CLIENT_SECRET,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def search_images(self, lat: float, lon: float, start: date, end: date, max_cloud_pct: float = 40.0) -> list[dict]:
        if not _has_credentials():
            # Dev fallback: one synthetic "scene" every ~5 days (Sentinel-2 revisit).
            scenes = []
            d = start
            while d <= end:
                scenes.append({"date": d.isoformat(), "cloud_cover_pct": 15.0, "product_id": f"synthetic-{d.isoformat()}", "is_synthetic": True})
                d += timedelta(days=5)
            return scenes

        import httpx

        token = self._get_token()
        bbox_pad = 0.001
        body = {
            "collections": ["sentinel-2-l2a"],
            "datetime": f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T23:59:59Z",
            "bbox": [lon - bbox_pad, lat - bbox_pad, lon + bbox_pad, lat + bbox_pad],
            "query": {"eo:cloud_cover": {"lt": max_cloud_pct}},
            "limit": 50,
        }
        resp = httpx.post(f"{CATALOG_URL}/search", json=body, headers={"Authorization": f"Bearer {token}"}, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        return [
            {
                "date": f["properties"]["datetime"][:10],
                "cloud_cover_pct": f["properties"].get("eo:cloud_cover"),
                "product_id": f["id"],
                "is_synthetic": False,
            }
            for f in features
        ]

    def vegetation_indices(self, lat: float, lon: float, target_date: date) -> dict[str, float]:
        if not _has_credentials():
            return {**_synthetic_indices(lat, lon, target_date), "is_synthetic": True}

        # Production path: Sentinel Hub Statistical API evalscript computing
        # NDVI/NDRE/EVI/SAVI/GNDVI/NDMI/NDWI/BSI from bands with cloud masking
        # (SCL band), returning a zonal mean over the field/cell geometry.
        # Left as an integration point — requires the field/cell polygon,
        # not just a point, so it's wired from services/ingestion at the
        # field level rather than called ad hoc per point.
        raise ProviderUnavailableError(
            "copernicus: Statistical API zonal evalscript wiring pending — requires field geometry, "
            "see services/ingestion.satellite_ingestion (Fase 2 hookup)"
        )
