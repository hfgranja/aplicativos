from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import CurrentUser, get_current_user, require_farm_in_tenant
from app.services import geo, ingestion
from app.services.analysis import compute_profitability, run_field_analysis

router = APIRouter(prefix="/fields", tags=["fields"])


def _get_owned_field(field_id: str, current_user: CurrentUser, db: Session) -> models.Field:
    f = db.query(models.Field).filter(models.Field.id == field_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Talhão não encontrado")
    farm = db.query(models.Farm).filter(models.Farm.id == f.farm_id).first()
    require_farm_in_tenant(farm, current_user)
    return f


def _create_field_row(db: Session, farm: models.Farm, name: str, boundary_geojson: dict, crop=None, season=None) -> models.Field:
    lat, lon, area_ha = geo.centroid_and_area_ha(boundary_geojson)
    field = models.Field(
        farm_id=farm.id,
        name=name,
        crop=crop,
        season=season,
        boundary_geojson=boundary_geojson,
        centroid_lat=lat,
        centroid_lon=lon,
        area_ha=area_ha,
    )
    db.add(field)
    return field


@router.post("", response_model=schemas.FieldOut)
def create_field(payload: schemas.FieldCreate, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = db.query(models.Farm).filter(models.Farm.id == payload.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada")
    require_farm_in_tenant(farm, current_user)

    lat, lon, area_ha = geo.centroid_and_area_ha(payload.boundary_geojson)
    field = models.Field(
        farm_id=farm.id,
        name=payload.name,
        crop=payload.crop,
        season=payload.season,
        planting_date=payload.planting_date,
        harvest_date_expected=payload.harvest_date_expected,
        boundary_geojson=payload.boundary_geojson,
        centroid_lat=lat,
        centroid_lon=lon,
        area_ha=area_ha,
        variable_cost_per_ha=payload.variable_cost_per_ha or 0.0,
        expected_price_per_kg=payload.expected_price_per_kg,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.post("/import", response_model=list[schemas.FieldOut])
def import_fields(payload: schemas.FieldImportRequest, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Bulk import field boundaries from a GeoJSON FeatureCollection
    (spec seção 59: "importação GeoJSON/KML" — KML/Shapefile conversion to
    GeoJSON happens client-side or in a future ingestion worker; this
    endpoint accepts standard GeoJSON)."""
    farm = db.query(models.Farm).filter(models.Farm.id == payload.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Fazenda não encontrada")
    require_farm_in_tenant(farm, current_user)

    geojson = payload.geojson
    features = geojson.get("features", [geojson]) if geojson.get("type") == "FeatureCollection" else [geojson]

    created = []
    for i, feat in enumerate(features):
        props = feat.get("properties", {}) or {}
        name = props.get("name") or props.get("id") or f"Talhão {i + 1}"
        field = _create_field_row(
            db, farm, name, feat,
            crop=props.get("crop", payload.default_crop),
            season=props.get("season", payload.default_season),
        )
        created.append(field)
    db.commit()
    for f in created:
        db.refresh(f)
    return created


@router.get("/{field_id}", response_model=schemas.FieldOut)
def get_field(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_field(field_id, current_user, db)


@router.get("/{field_id}/analysis")
def field_analysis(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    field = _get_owned_field(field_id, current_user, db)
    result = run_field_analysis(db, field, persist=True)
    return {
        "field_id": field.id,
        "prediction": result["prediction"],
        "confidence_score": result["confidence_score"],
        "confidence_tier": result["confidence_tier"],
        "recommendations": result["recommendations"],
        "features": {k: v for k, v in result["features"].items() if not k.startswith("_")},
    }


@router.get("/{field_id}/satellite", response_model=list[schemas.SatelliteObservationOut])
def field_satellite(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    field = _get_owned_field(field_id, current_user, db)
    ingestion.ensure_satellite_ingested(db, field)
    return (
        db.query(models.SatelliteObservation)
        .filter(models.SatelliteObservation.field_id == field.id)
        .order_by(models.SatelliteObservation.date)
        .all()
    )


@router.get("/{field_id}/weather", response_model=list[schemas.WeatherObservationOut])
def field_weather(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    field = _get_owned_field(field_id, current_user, db)
    ingestion.ensure_weather_ingested(db, field)
    return (
        db.query(models.WeatherObservation)
        .filter(models.WeatherObservation.field_id == field.id)
        .order_by(models.WeatherObservation.date)
        .all()
    )


@router.get("/{field_id}/soil", response_model=list[schemas.SoilSampleOut])
def field_soil(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    field = _get_owned_field(field_id, current_user, db)
    ingestion.ensure_soil_ingested(db, field)
    return db.query(models.SoilSample).filter(models.SoilSample.field_id == field.id).all()


@router.get("/{field_id}/yield-forecast", response_model=schemas.PredictionOut)
def field_yield_forecast(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    field = _get_owned_field(field_id, current_user, db)
    run_field_analysis(db, field, persist=True)
    prediction = (
        db.query(models.Prediction)
        .filter(models.Prediction.field_id == field.id)
        .order_by(models.Prediction.generated_at.desc())
        .first()
    )
    return prediction


@router.get("/{field_id}/profitability", response_model=schemas.ProfitabilityOut)
def field_profitability(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    field = _get_owned_field(field_id, current_user, db)
    result = run_field_analysis(db, field, persist=True)
    return compute_profitability(field, result["prediction"])


@router.get("/{field_id}/recommendations", response_model=list[schemas.RecommendationOut])
def field_recommendations(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    field = _get_owned_field(field_id, current_user, db)
    run_field_analysis(db, field, persist=True)
    return (
        db.query(models.Recommendation)
        .filter(models.Recommendation.field_id == field.id, models.Recommendation.status == "open")
        .order_by(models.Recommendation.expected_margin_delta_per_ha.desc())
        .all()
    )
