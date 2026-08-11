from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import CurrentUser, get_current_user, require_farm_in_tenant
from app.services import economic_engine, monte_carlo
from app.services.analysis import run_field_analysis

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("", response_model=schemas.ScenarioOut)
def create_scenario(payload: schemas.ScenarioInput, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """What-if simulator (spec seção 25/27): compares Baseline vs Scenario
    after altering fertilizer, irrigation, planting date, seed population,
    intervention/commodity price and expected rainfall."""
    field = db.query(models.Field).filter(models.Field.id == payload.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Talhão não encontrado")
    farm = db.query(models.Farm).filter(models.Farm.id == field.farm_id).first()
    require_farm_in_tenant(farm, current_user)

    result = run_field_analysis(db, field, persist=False)
    prediction = result["prediction"]

    price = payload.commodity_price_override or field.expected_price_per_kg or 0.0
    variable_cost = field.variable_cost_per_ha or 0.0

    baseline_margin = economic_engine.contribution_margin_per_ha(prediction["yield_expected_kg_ha"], price, variable_cost)

    # Combine the explicit agronomic response assumption with lightweight
    # deltas for rainfall/fertilizer/irrigation/population/planting-date
    # shift, each contributing a bounded % adjustment to expected yield.
    response_pct = payload.yield_response_pct or 0.0
    response_pct += (payload.fertilizer_dose_delta_pct or 0) * 0.15
    response_pct += min(max(payload.irrigation_mm_delta or 0, -100), 100) / 100 * 0.10
    response_pct += (payload.seed_population_delta_pct or 0) * 0.08
    response_pct += min(max(payload.expected_rainfall_delta_pct or 0, -50), 50) / 100 * 0.20
    response_pct -= abs(payload.planting_date_shift_days or 0) * 0.002  # deviating from optimal window costs yield

    scenario_yield = prediction["yield_expected_kg_ha"] * (1 + response_pct)
    intervention_cost = payload.intervention_cost_per_ha or 0.0
    scenario_margin = economic_engine.contribution_margin_per_ha(scenario_yield, price, variable_cost + intervention_cost)
    incremental_margin = economic_engine.incremental_margin_per_ha(scenario_margin, baseline_margin)
    roi_value = economic_engine.roi(incremental_margin, intervention_cost)

    mc = monte_carlo.simulate(
        yield_p10_kg_ha=prediction["yield_p10_kg_ha"],
        yield_p50_kg_ha=prediction["yield_expected_kg_ha"],
        yield_p90_kg_ha=prediction["yield_p90_kg_ha"],
        price_per_kg=price,
        variable_cost_per_ha=variable_cost,
        intervention_cost_per_ha=intervention_cost,
        yield_response_pct=response_pct,
        n_simulations=payload.n_simulations or 1000,
    )

    scenario = models.Scenario(
        field_id=field.id,
        name=payload.name,
        inputs=payload.model_dump(),
        baseline_margin_per_ha=baseline_margin,
        scenario_margin_per_ha=scenario_margin,
        incremental_margin_per_ha=incremental_margin,
        intervention_cost_per_ha=intervention_cost,
        roi=roi_value,
        break_even_price=economic_engine.break_even_price(variable_cost + intervention_cost, scenario_yield),
        break_even_yield=economic_engine.break_even_yield(variable_cost + intervention_cost, price),
        monte_carlo=mc,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/{field_id}", response_model=list[schemas.ScenarioOut])
def list_scenarios(field_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    field = db.query(models.Field).filter(models.Field.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Talhão não encontrado")
    farm = db.query(models.Farm).filter(models.Farm.id == field.farm_id).first()
    require_farm_in_tenant(farm, current_user)
    return (
        db.query(models.Scenario)
        .filter(models.Scenario.field_id == field_id)
        .order_by(models.Scenario.created_at.desc())
        .all()
    )
