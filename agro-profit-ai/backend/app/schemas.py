from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str
    full_name: str
    role: str


# ---------- Farm ----------

class FarmCreate(BaseModel):
    name: str
    state: Optional[str] = None
    municipality: Optional[str] = None
    ibge_municipality_code: Optional[str] = None
    boundary_geojson: Optional[dict] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    area_ha: Optional[float] = None


class FarmOut(BaseModel):
    id: str
    name: str
    state: Optional[str]
    municipality: Optional[str]
    ibge_municipality_code: Optional[str]
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]
    boundary_geojson: Optional[dict]
    area_ha: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Field ----------

class FieldCreate(BaseModel):
    farm_id: str
    name: str
    crop: Optional[str] = None
    season: Optional[str] = None
    planting_date: Optional[datetime] = None
    harvest_date_expected: Optional[datetime] = None
    boundary_geojson: dict
    variable_cost_per_ha: Optional[float] = 0.0
    expected_price_per_kg: Optional[float] = None


class FieldImportRequest(BaseModel):
    farm_id: str
    geojson: dict
    default_crop: Optional[str] = None
    default_season: Optional[str] = None


class FieldOut(BaseModel):
    id: str
    farm_id: str
    name: str
    crop: Optional[str]
    season: Optional[str]
    planting_date: Optional[datetime]
    harvest_date_expected: Optional[datetime]
    boundary_geojson: dict
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]
    area_ha: Optional[float]
    variable_cost_per_ha: Optional[float]
    expected_price_per_kg: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Soil ----------

class SoilSampleIn(BaseModel):
    field_id: str
    sample_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sample_date: Optional[datetime] = None
    depth_cm: Optional[str] = None
    ph: Optional[float] = None
    organic_matter: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    calcium: Optional[float] = None
    magnesium: Optional[float] = None
    aluminum: Optional[float] = None
    cec: Optional[float] = None
    base_saturation: Optional[float] = None
    clay: Optional[float] = None
    sand: Optional[float] = None
    silt: Optional[float] = None


class SoilSampleOut(SoilSampleIn):
    id: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Yield ----------

class YieldRecordIn(BaseModel):
    field_id: str
    season: str
    crop: str
    yield_kg_ha: float
    area_ha: Optional[float] = None
    harvest_date: Optional[datetime] = None
    source: Optional[str] = "producer_upload"


class YieldRecordOut(YieldRecordIn):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Operations ----------

class OperationIn(BaseModel):
    field_id: str
    season: Optional[str] = None
    operation_type: str
    description: Optional[str] = None
    product: Optional[str] = None
    dose: Optional[float] = None
    dose_unit: Optional[str] = None
    application_date: Optional[datetime] = None
    cost_per_ha: Optional[float] = 0.0
    fuel_liters: Optional[float] = None
    labor_hours: Optional[float] = None


class OperationOut(OperationIn):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Weather / Satellite (read models) ----------

class WeatherObservationOut(BaseModel):
    date: datetime
    kind: str
    provider: str
    station_distance_km: Optional[float]
    precipitation_mm: Optional[float]
    temperature_min_c: Optional[float]
    temperature_max_c: Optional[float]
    temperature_avg_c: Optional[float]
    relative_humidity_pct: Optional[float]
    solar_radiation_mj_m2: Optional[float]
    wind_speed_ms: Optional[float]

    model_config = {"from_attributes": True}


class SatelliteObservationOut(BaseModel):
    date: datetime
    provider: str
    cloud_cover_pct: Optional[float]
    ndvi: Optional[float]
    ndre: Optional[float]
    evi: Optional[float]
    savi: Optional[float]
    gndvi: Optional[float]
    ndmi: Optional[float]
    ndwi: Optional[float]
    bsi: Optional[float]
    is_synthetic: bool

    model_config = {"from_attributes": True}


# ---------- Prediction / Analysis ----------

class ShapFactor(BaseModel):
    feature: str
    label: str
    contribution_kg_ha: float


class PredictionOut(BaseModel):
    id: str
    field_id: str
    generated_at: datetime
    model_id: Optional[str]
    model_version: Optional[str]
    yield_expected_kg_ha: Optional[float]
    yield_p10_kg_ha: Optional[float]
    yield_p50_kg_ha: Optional[float]
    yield_p90_kg_ha: Optional[float]
    confidence_score: Optional[float]
    confidence_tier: Optional[str]
    risk_level: Optional[str]
    anomaly_flag: Optional[str]
    shap_explanation: Optional[list]

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class ProfitabilityOut(BaseModel):
    field_id: str
    yield_expected_kg_ha: float
    expected_price_per_kg: float
    gross_revenue_per_ha: float
    variable_cost_per_ha: float
    contribution_margin_per_ha: float
    total_area_ha: float
    total_expected_margin: float
    break_even_yield_kg_ha: float
    break_even_price_per_kg: float
    downside_margin_per_ha: float  # margin at P10 yield
    upside_margin_per_ha: float  # margin at P90 yield


class RecommendationOut(BaseModel):
    id: str
    field_id: str
    zone_id: Optional[str]
    priority: str
    issue: str
    evidence: list
    suggested_action: str
    estimated_cost_per_ha: float
    expected_yield_delta_kg_ha: float
    expected_margin_delta_per_ha: float
    expected_roi: float
    confidence: float
    decision: str
    model_version: Optional[str]
    generated_at: datetime
    status: str

    model_config = {"from_attributes": True, "protected_namespaces": ()}


# ---------- Scenario (what-if) ----------

class ScenarioInput(BaseModel):
    field_id: str
    name: Optional[str] = "Scenario"
    fertilizer_dose_delta_pct: Optional[float] = 0.0
    irrigation_mm_delta: Optional[float] = 0.0
    planting_date_shift_days: Optional[int] = 0
    seed_population_delta_pct: Optional[float] = 0.0
    intervention_cost_per_ha: Optional[float] = 0.0
    commodity_price_override: Optional[float] = None
    expected_rainfall_delta_pct: Optional[float] = 0.0
    yield_response_pct: Optional[float] = 0.0  # expected agronomic response of the intervention
    n_simulations: Optional[int] = 1000


class MonteCarloOut(BaseModel):
    p5_margin_per_ha: float
    p50_margin_per_ha: float
    p95_margin_per_ha: float
    probability_of_profit: float
    probability_of_positive_intervention_roi: float


class ScenarioOut(BaseModel):
    id: str
    field_id: str
    name: Optional[str]
    inputs: dict
    baseline_margin_per_ha: float
    scenario_margin_per_ha: float
    incremental_margin_per_ha: float
    intervention_cost_per_ha: float
    roi: Optional[float]
    break_even_price: float
    break_even_yield: float
    monte_carlo: MonteCarloOut
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Alerts ----------

class AlertOut(BaseModel):
    id: str
    field_id: str
    kind: str
    severity: str
    message: str
    triggered_at: datetime
    acknowledged: bool

    model_config = {"from_attributes": True}


# ---------- Executive dashboard ----------

class FarmHealthOut(BaseModel):
    farm_id: str
    farm_name: str
    farm_health_score: float
    total_area_ha: float
    expected_yield_kg_ha: float
    expected_revenue: float
    expected_margin: float
    area_at_risk_ha: float
    potential_economic_loss: float
    potential_recoverable_margin: float
    weather_risk: str
    fields_count: int
    open_recommendations: int
    open_alerts: int
