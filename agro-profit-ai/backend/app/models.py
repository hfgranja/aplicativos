import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# NOTE on geometry storage: boundaries/points are stored as GeoJSON in JSON
# columns so the MVP runs on plain SQLite with zero native deps. In
# production (DATABASE_URL pointing at PostgreSQL + PostGIS) these columns
# should be migrated to GeoAlchemy2 `Geometry` columns for spatial indexing
# and server-side spatial queries (ST_Intersects, ST_Area, etc.) — see
# docs/DESIGN.md section "Geospatial model".


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=_now)

    farms = relationship("Farm", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="Owner")  # Owner, FarmManager, Agronomist, Analyst, Operator, Viewer, Admin
    created_at = Column(DateTime, default=_now)

    tenant = relationship("Tenant", back_populates="users")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    state = Column(String)
    municipality = Column(String)
    ibge_municipality_code = Column(String)
    centroid_lat = Column(Float)
    centroid_lon = Column(Float)
    boundary_geojson = Column(JSON)  # Polygon/MultiPolygon GeoJSON
    area_ha = Column(Float)
    created_at = Column(DateTime, default=_now)

    tenant = relationship("Tenant", back_populates="farms")
    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")


class Field(Base):
    __tablename__ = "fields"

    id = Column(String, primary_key=True, default=_uuid)
    farm_id = Column(String, ForeignKey("farms.id"), nullable=False)
    name = Column(String, nullable=False)
    crop = Column(String)
    season = Column(String)  # e.g. "2025/2026"
    planting_date = Column(DateTime)
    harvest_date_expected = Column(DateTime)
    boundary_geojson = Column(JSON, nullable=False)
    centroid_lat = Column(Float)
    centroid_lon = Column(Float)
    area_ha = Column(Float)
    variable_cost_per_ha = Column(Float, default=0.0)  # seeds+fert+defensives+ops excl. new intervention
    expected_price_per_kg = Column(Float)  # commodity price used for margin calc
    created_at = Column(DateTime, default=_now)

    farm = relationship("Farm", back_populates="fields")
    management_zones = relationship("ManagementZone", back_populates="field", cascade="all, delete-orphan")
    soil_samples = relationship("SoilSample", back_populates="field", cascade="all, delete-orphan")
    yield_records = relationship("YieldRecord", back_populates="field", cascade="all, delete-orphan")
    operations = relationship("Operation", back_populates="field", cascade="all, delete-orphan")
    satellite_observations = relationship("SatelliteObservation", back_populates="field", cascade="all, delete-orphan")
    weather_observations = relationship("WeatherObservation", back_populates="field", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="field", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="field", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="field", cascade="all, delete-orphan")


class ManagementZone(Base):
    __tablename__ = "management_zones"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    name = Column(String)
    boundary_geojson = Column(JSON)
    area_ha = Column(Float)

    field = relationship("Field", back_populates="management_zones")
    cells = relationship("SpatialCell", back_populates="zone", cascade="all, delete-orphan")


class SpatialCell(Base):
    """Grid cell — the fundamental spatial+temporal unit (spec section 1/8)."""

    __tablename__ = "spatial_cells"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    zone_id = Column(String, ForeignKey("management_zones.id"), nullable=True)
    grid_resolution_m = Column(Integer, default=30)
    row_index = Column(Integer)
    col_index = Column(Integer)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    boundary_geojson = Column(JSON)
    area_ha = Column(Float)
    elevation_m = Column(Float)
    slope_pct = Column(Float)

    zone = relationship("ManagementZone", back_populates="cells")


class SoilSample(Base):
    __tablename__ = "soil_samples"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    sample_id = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    sample_date = Column(DateTime)
    depth_cm = Column(String)  # e.g. "0-20"
    ph = Column(Float)
    organic_matter = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    calcium = Column(Float)
    magnesium = Column(Float)
    aluminum = Column(Float)
    cec = Column(Float)
    base_saturation = Column(Float)
    clay = Column(Float)
    sand = Column(Float)
    silt = Column(Float)
    source = Column(String, default="laboratory")  # laboratory | soilgrids | mapbiomas
    created_at = Column(DateTime, default=_now)

    field = relationship("Field", back_populates="soil_samples")


class YieldRecord(Base):
    __tablename__ = "yield_records"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    season = Column(String, nullable=False)
    crop = Column(String, nullable=False)
    yield_kg_ha = Column(Float, nullable=False)
    area_ha = Column(Float)
    harvest_date = Column(DateTime)
    source = Column(String, default="producer_upload")  # producer_upload | harvester_map | ibge_benchmark
    created_at = Column(DateTime, default=_now)

    field = relationship("Field", back_populates="yield_records")


class Operation(Base):
    """Planting, fertilization, defensives, irrigation, machine ops — spec section 5."""

    __tablename__ = "operations"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    season = Column(String)
    operation_type = Column(String, nullable=False)  # planting | fertilization | defensive | irrigation | machine | harvest
    description = Column(String)
    product = Column(String)
    dose = Column(Float)
    dose_unit = Column(String)
    application_date = Column(DateTime)
    cost_per_ha = Column(Float, default=0.0)
    fuel_liters = Column(Float)
    labor_hours = Column(Float)
    created_at = Column(DateTime, default=_now)

    field = relationship("Field", back_populates="operations")


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    kind = Column(String, default="observation")  # observation | forecast
    provider = Column(String, nullable=False)  # inmet | nasa_power | chirps | era5 | openweather | tomorrow | open-meteo
    station_distance_km = Column(Float)
    precipitation_mm = Column(Float)
    temperature_min_c = Column(Float)
    temperature_max_c = Column(Float)
    temperature_avg_c = Column(Float)
    relative_humidity_pct = Column(Float)
    solar_radiation_mj_m2 = Column(Float)
    wind_speed_ms = Column(Float)
    created_at = Column(DateTime, default=_now)

    field = relationship("Field", back_populates="weather_observations")


class SatelliteObservation(Base):
    __tablename__ = "satellite_observations"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    cell_id = Column(String, ForeignKey("spatial_cells.id"), nullable=True)
    date = Column(DateTime, nullable=False)
    provider = Column(String, default="copernicus_sentinel2")
    cloud_cover_pct = Column(Float)
    ndvi = Column(Float)
    ndre = Column(Float)
    evi = Column(Float)
    savi = Column(Float)
    gndvi = Column(Float)
    ndmi = Column(Float)
    ndwi = Column(Float)
    bsi = Column(Float)
    is_synthetic = Column(Boolean, default=False)  # true when generated by dev fallback, not real imagery
    created_at = Column(DateTime, default=_now)

    field = relationship("Field", back_populates="satellite_observations")


class CommodityPrice(Base):
    __tablename__ = "commodity_prices"

    id = Column(String, primary_key=True, default=_uuid)
    crop = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    currency = Column(String, default="BRL")
    source = Column(String, default="manual")


class Prediction(Base):
    """Yield forecast + risk + confidence output — spec sections 19-25."""

    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    generated_at = Column(DateTime, default=_now)
    model_id = Column(String)
    model_version = Column(String)
    feature_snapshot_id = Column(String)
    yield_expected_kg_ha = Column(Float)
    yield_p10_kg_ha = Column(Float)
    yield_p50_kg_ha = Column(Float)
    yield_p90_kg_ha = Column(Float)
    confidence_score = Column(Float)  # 0-100
    confidence_tier = Column(String)  # LOW | MEDIUM | HIGHER
    risk_level = Column(String)  # normal | watch | high | critical
    anomaly_flag = Column(String)
    shap_explanation = Column(JSON)  # list of {feature, contribution_kg_ha}
    feature_values = Column(JSON)

    field = relationship("Field", back_populates="predictions")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    zone_id = Column(String, ForeignKey("management_zones.id"), nullable=True)
    priority = Column(String)  # high | medium | low
    issue = Column(String)
    evidence = Column(JSON)  # list of strings
    suggested_action = Column(String)
    estimated_cost_per_ha = Column(Float)
    expected_yield_delta_kg_ha = Column(Float)
    expected_margin_delta_per_ha = Column(Float)
    expected_roi = Column(Float)
    confidence = Column(Float)
    decision = Column(String)  # ACTION | MONITOR | DO_NOT_ACT
    model_version = Column(String)
    generated_at = Column(DateTime, default=_now)
    status = Column(String, default="open")  # open | accepted | dismissed

    field = relationship("Field", back_populates="recommendations")


class Scenario(Base):
    """What-if simulation run — spec section 25/27."""

    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    name = Column(String)
    inputs = Column(JSON)  # fertilizer/irrigation/planting_date/population/cost/price/rainfall overrides
    baseline_margin_per_ha = Column(Float)
    scenario_margin_per_ha = Column(Float)
    incremental_margin_per_ha = Column(Float)
    intervention_cost_per_ha = Column(Float)
    roi = Column(Float)
    break_even_price = Column(Float)
    break_even_yield = Column(Float)
    monte_carlo = Column(JSON)  # {p5, p50, p95, probability_of_profit, probability_of_positive_roi}
    created_at = Column(DateTime, default=_now)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=_uuid)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False)
    kind = Column(String, nullable=False)  # rain_forecast|drought_risk|heat_risk|ndvi_anomaly|soil_moisture|yield_deterioration|negative_margin
    severity = Column(String, default="info")  # info | warning | critical
    message = Column(String, nullable=False)
    triggered_at = Column(DateTime, default=_now)
    acknowledged = Column(Boolean, default=False)

    field = relationship("Field", back_populates="alerts")


class DataQualityLog(Base):
    """Lineage + data quality record — spec sections 46-47."""

    __tablename__ = "data_quality_logs"

    id = Column(String, primary_key=True, default=_uuid)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    source = Column(String)
    provider = Column(String)
    quality_score = Column(Float)
    issues = Column(JSON)
    ingested_at = Column(DateTime, default=_now)
    license = Column(String)
