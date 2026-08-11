"""Demo tenant/user/farm/field seed — mirrors spec seção 71 "Definição de
Done": lets a fresh install immediately show a farm with fields, a map,
predictions, profitability and recommendations without manual setup."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app import models
from app.security import hash_password

DEMO_EMAIL = "demo@agroprofit.ai"
DEMO_PASSWORD = "agro123"

# Two illustrative fields near Rio Verde, GO — a strong soja/milho region.
FIELD_A_BOUNDARY = {
    "type": "Feature",
    "properties": {"name": "Talhão Norte"},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-50.9270, -17.7980],
            [-50.9150, -17.7980],
            [-50.9150, -17.8080],
            [-50.9270, -17.8080],
            [-50.9270, -17.7980],
        ]],
    },
}
FIELD_B_BOUNDARY = {
    "type": "Feature",
    "properties": {"name": "Talhão Sul"},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-50.9270, -17.8120],
            [-50.9140, -17.8120],
            [-50.9140, -17.8230],
            [-50.9270, -17.8230],
            [-50.9270, -17.8120],
        ]],
    },
}
FARM_BOUNDARY = {
    "type": "Feature",
    "properties": {"name": "Fazenda Santa Fé"},
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-50.9290, -17.7960],
            [-50.9120, -17.7960],
            [-50.9120, -17.8250],
            [-50.9290, -17.8250],
            [-50.9290, -17.7960],
        ]],
    },
}


def seed_if_empty(db: Session) -> None:
    if db.query(models.Tenant).count() > 0:
        return

    from app.services import geo

    tenant = models.Tenant(name="Fazenda Santa Fé Agropecuária")
    db.add(tenant)
    db.flush()

    user = models.User(
        tenant_id=tenant.id,
        email=DEMO_EMAIL,
        hashed_password=hash_password(DEMO_PASSWORD),
        full_name="Produtor Demo",
        role="Owner",
    )
    db.add(user)

    farm_lat, farm_lon, farm_area = geo.centroid_and_area_ha(FARM_BOUNDARY)
    farm = models.Farm(
        tenant_id=tenant.id,
        name="Fazenda Santa Fé",
        state="GO",
        municipality="Rio Verde",
        ibge_municipality_code="5218805",
        boundary_geojson=FARM_BOUNDARY,
        centroid_lat=farm_lat,
        centroid_lon=farm_lon,
        area_ha=farm_area,
    )
    db.add(farm)
    db.flush()

    now = datetime.now(timezone.utc)
    fields_spec = [
        (FIELD_A_BOUNDARY, "Talhão Norte", "soja", 900.0, 3.85),
        (FIELD_B_BOUNDARY, "Talhão Sul", "milho", 1450.0, 0.95),
    ]
    fields = []
    for boundary, name, crop, variable_cost, price in fields_spec:
        lat, lon, area = geo.centroid_and_area_ha(boundary)
        f = models.Field(
            farm_id=farm.id,
            name=name,
            crop=crop,
            season="2025/2026",
            planting_date=now - timedelta(days=45),
            harvest_date_expected=now + timedelta(days=90),
            boundary_geojson=boundary,
            centroid_lat=lat,
            centroid_lon=lon,
            area_ha=area,
            variable_cost_per_ha=variable_cost,
            expected_price_per_kg=price,
        )
        db.add(f)
        fields.append(f)
    db.flush()

    for crop, price in (("soja", 3.85), ("milho", 0.95)):
        db.add(models.CommodityPrice(crop=crop, date=now, price_per_kg=price, source="manual"))

    # One prior season of realized yield per field, so the demo shows
    # confidence tier moving from LOW toward MEDIUM and the margin history.
    for f, base_yield in zip(fields, (3100.0, 5300.0)):
        db.add(
            models.YieldRecord(
                field_id=f.id,
                season="2024/2025",
                crop=f.crop,
                yield_kg_ha=base_yield,
                area_ha=f.area_ha,
                harvest_date=now - timedelta(days=270),
                source="producer_upload",
            )
        )
        db.add(
            models.SoilSample(
                field_id=f.id,
                sample_id="LAB-2025-001",
                latitude=f.centroid_lat,
                longitude=f.centroid_lon,
                sample_date=now - timedelta(days=60),
                depth_cm="0-20",
                ph=5.6,
                organic_matter=28.0,
                phosphorus=12.5,
                potassium=0.28,
                calcium=3.2,
                magnesium=1.1,
                cec=9.4,
                base_saturation=52.0,
                clay=38.0,
                sand=35.0,
                silt=27.0,
                source="laboratory",
            )
        )
        db.add(
            models.Operation(
                field_id=f.id,
                season=f.season,
                operation_type="fertilization",
                description="Adubação de base NPK",
                product="NPK 08-28-16",
                dose=300,
                dose_unit="kg/ha",
                application_date=now - timedelta(days=44),
                cost_per_ha=520.0,
            )
        )

    db.commit()
