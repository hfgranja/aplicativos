from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import CurrentUser, get_current_user, require_farm_in_tenant
from app.services import geo
from app.services.analysis import compute_profitability, run_field_analysis

router = APIRouter(prefix="/farms", tags=["farms"])


@router.get("", response_model=list[schemas.FarmOut])
def list_farms(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Farm).filter(models.Farm.tenant_id == current_user.tenant_id).all()


@router.post("", response_model=schemas.FarmOut)
def create_farm(payload: schemas.FarmCreate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    lat, lon, area_ha = payload.centroid_lat, payload.centroid_lon, payload.area_ha
    if payload.boundary_geojson and (lat is None or lon is None):
        lat, lon, area_ha = geo.centroid_and_area_ha(payload.boundary_geojson)

    farm = models.Farm(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        state=payload.state,
        municipality=payload.municipality,
        ibge_municipality_code=payload.ibge_municipality_code,
        boundary_geojson=payload.boundary_geojson,
        centroid_lat=lat,
        centroid_lon=lon,
        area_ha=area_ha,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/{farm_id}", response_model=schemas.FarmOut)
def get_farm(farm_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada")
    require_farm_in_tenant(farm, current_user)
    return farm


@router.get("/{farm_id}/fields", response_model=list[schemas.FieldOut])
def list_farm_fields(farm_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada")
    require_farm_in_tenant(farm, current_user)
    return db.query(models.Field).filter(models.Field.farm_id == farm.id).all()


@router.get("/{farm_id}/health", response_model=schemas.FarmHealthOut)
def farm_health(farm_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Executive dashboard KPIs (spec seção 30/68) — answers in one call:
    expected yield/revenue/margin, area at risk, potential loss/recovery."""
    farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada")
    require_farm_in_tenant(farm, current_user)

    fields = db.query(models.Field).filter(models.Field.farm_id == farm.id).all()
    if not fields:
        return schemas.FarmHealthOut(
            farm_id=farm.id,
            farm_name=farm.name,
            farm_health_score=0,
            total_area_ha=farm.area_ha or 0,
            expected_yield_kg_ha=0,
            expected_revenue=0,
            expected_margin=0,
            area_at_risk_ha=0,
            potential_economic_loss=0,
            potential_recoverable_margin=0,
            weather_risk="unknown",
            fields_count=0,
            open_recommendations=0,
            open_alerts=0,
        )

    total_area = 0.0
    total_revenue = 0.0
    total_margin = 0.0
    area_at_risk = 0.0
    potential_loss = 0.0
    recoverable_margin = 0.0
    yield_weighted_sum = 0.0
    risk_flags = []
    open_recs = 0
    open_alerts = 0

    for f in fields:
        result = run_field_analysis(db, f, persist=True)
        profitability = compute_profitability(f, result["prediction"])
        area = f.area_ha or 0.0
        total_area += area
        total_revenue += profitability["gross_revenue_per_ha"] * area
        total_margin += profitability["contribution_margin_per_ha"] * area
        yield_weighted_sum += result["prediction"]["yield_expected_kg_ha"] * area

        if result["prediction"]["risk_level"] in ("high", "critical"):
            area_at_risk += area
            downside_loss_per_ha = profitability["contribution_margin_per_ha"] - profitability["downside_margin_per_ha"]
            potential_loss += max(downside_loss_per_ha, 0) * area
        risk_flags.append(result["prediction"]["risk_level"])

        for rec in result["recommendations"]:
            if rec["decision"] == "ACTION":
                recoverable_margin += max(rec["expected_margin_delta_per_ha"], 0) * area
                open_recs += 1

        open_alerts += db.query(models.Alert).filter(models.Alert.field_id == f.id, models.Alert.acknowledged.is_(False)).count()

    weather_risk = "high" if "critical" in risk_flags else ("medium" if "high" in risk_flags else "low")
    health_score = round(max(0, 100 - (area_at_risk / total_area * 100 if total_area else 0) * 0.8), 1)

    return schemas.FarmHealthOut(
        farm_id=farm.id,
        farm_name=farm.name,
        farm_health_score=health_score,
        total_area_ha=round(total_area, 2),
        expected_yield_kg_ha=round(yield_weighted_sum / total_area, 1) if total_area else 0,
        expected_revenue=round(total_revenue, 2),
        expected_margin=round(total_margin, 2),
        area_at_risk_ha=round(area_at_risk, 2),
        potential_economic_loss=round(potential_loss, 2),
        potential_recoverable_margin=round(recoverable_margin, 2),
        weather_risk=weather_risk,
        fields_count=len(fields),
        open_recommendations=open_recs,
        open_alerts=open_alerts,
    )
