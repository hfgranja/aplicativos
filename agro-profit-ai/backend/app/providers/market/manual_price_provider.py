"""MarketPriceProvider — MVP implementation backed by our own DB.

The spec does not point at a single reliably free, no-auth commodity price
API (CEPEA/B3 feeds require paid access or scraping their site, which is
fragile and outside the "verifiable free source" bar set for this project).
For the MVP, prices are entered by the tenant (per field or globally per
crop) via /data endpoints and stored in CommodityPrice. This keeps the
MarketPriceProvider interface real and swappable — a future CEPEA/B3
adapter can implement the same interface without touching the Economic
Engine.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app import models
from app.providers.base import MarketPriceProvider


class ManualPriceProvider(MarketPriceProvider):
    name = "manual"

    def __init__(self, db: Session):
        self.db = db

    def historical_prices(self, crop: str, start: date, end: date) -> list[dict]:
        rows = (
            self.db.query(models.CommodityPrice)
            .filter(models.CommodityPrice.crop == crop)
            .filter(models.CommodityPrice.date >= start, models.CommodityPrice.date <= end)
            .order_by(models.CommodityPrice.date)
            .all()
        )
        return [{"date": r.date.isoformat(), "price_per_kg": r.price_per_kg, "currency": r.currency} for r in rows]

    def current_price(self, crop: str) -> float | None:
        row = (
            self.db.query(models.CommodityPrice)
            .filter(models.CommodityPrice.crop == crop)
            .order_by(models.CommodityPrice.date.desc())
            .first()
        )
        return row.price_per_kg if row else None
