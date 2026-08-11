"""FarmDataProvider — reads producer-uploaded operational data (spec 4).

This is the provider wrapping our own proprietary data (Farm Data Hub),
which the product strategy identifies as the real long-term moat: the
history connecting soil + weather + satellite + management + realized
yield + cost + price + margin, season over season.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app import models
from app.providers.base import FarmDataProvider


class DbFarmDataProvider(FarmDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def operations(self, field_id: str, season: Optional[str] = None) -> list[dict]:
        q = self.db.query(models.Operation).filter(models.Operation.field_id == field_id)
        if season:
            q = q.filter(models.Operation.season == season)
        return [
            {
                "operation_type": o.operation_type,
                "product": o.product,
                "dose": o.dose,
                "dose_unit": o.dose_unit,
                "application_date": o.application_date.isoformat() if o.application_date else None,
                "cost_per_ha": o.cost_per_ha,
            }
            for o in q.all()
        ]

    def yield_history(self, field_id: str) -> list[dict]:
        rows = self.db.query(models.YieldRecord).filter(models.YieldRecord.field_id == field_id).all()
        return [
            {"season": r.season, "crop": r.crop, "yield_kg_ha": r.yield_kg_ha, "source": r.source}
            for r in rows
        ]
