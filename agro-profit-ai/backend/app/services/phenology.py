"""Motor de fenologia (spec seção 35).

Determina o estágio fenológico atual a partir da data de plantio e do
acúmulo real de graus-dia (GDD) sobre as observações climáticas ingeridas,
e agrega as features climáticas POR FASE — a mesma chuva de 40 mm vale
coisas muito diferentes no vegetativo e no florescimento, e o modelo de
estresse hídrico pondera o déficit pela sensibilidade da fase
(water_sensitivity da base de conhecimento).

GDD diário = max(0, min(Tmax, Tupper) média com Tmin − Tbase), método
simples de média truncada — consistente com a prática FAO-56 revisada de
estimar duração de fases por GDD em vez de dias-calendário.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.domain.crop_knowledge import CropKnowledge, get_crop_knowledge, stage_for_gdd


def daily_gdd(t_min: float | None, t_max: float | None, kb: CropKnowledge) -> float:
    if t_min is None or t_max is None:
        return 0.0
    t_max_capped = min(t_max, kb.t_upper_c)
    t_mean = (max(t_min, kb.t_base_c) + max(t_max_capped, kb.t_base_c)) / 2
    return max(0.0, t_mean - kb.t_base_c)


def compute_phenology(db: Session, field: models.Field) -> dict:
    """Retorna estágio atual, GDD acumulado, progresso do ciclo e a série de
    features climáticas agregadas por fase desde o plantio."""
    kb = get_crop_knowledge(field.crop)

    if not field.planting_date:
        return {"available": False, "reason": "sem data de plantio cadastrada", "crop_kb": kb.crop}

    obs = (
        db.query(models.WeatherObservation)
        .filter(
            models.WeatherObservation.field_id == field.id,
            models.WeatherObservation.kind == "observation",
            models.WeatherObservation.date >= field.planting_date,
        )
        .order_by(models.WeatherObservation.date)
        .all()
    )
    if not obs:
        return {"available": False, "reason": "sem observações climáticas desde o plantio", "crop_kb": kb.crop}

    accumulated = 0.0
    per_stage: dict[str, dict] = {}
    stage_first_date: dict[str, str] = {}

    for o in obs:
        gdd = daily_gdd(o.temperature_min_c, o.temperature_max_c, kb)
        accumulated += gdd
        stage = stage_for_gdd(kb, accumulated)
        bucket = per_stage.setdefault(
            stage.name,
            {"rain_mm": 0.0, "gdd": 0.0, "days": 0, "heat_stress_days": 0, "dry_days": 0},
        )
        bucket["rain_mm"] += o.precipitation_mm or 0.0
        bucket["gdd"] += gdd
        bucket["days"] += 1
        if (o.temperature_max_c or 0) >= kb.heat_stress_c:
            bucket["heat_stress_days"] += 1
        if (o.precipitation_mm or 0.0) < 1.0:
            bucket["dry_days"] += 1
        stage_first_date.setdefault(stage.name, o.date.date().isoformat())

    current_stage = stage_for_gdd(kb, accumulated)
    cycle_progress = min(1.0, accumulated / kb.cycle_gdd)

    # Estresse térmico em fase crítica: dias de calor ponderados pela
    # sensibilidade hídrica da fase (proxy de sensibilidade geral da fase).
    critical_heat_days = sum(
        bucket["heat_stress_days"]
        for name, bucket in per_stage.items()
        if _stage_sensitivity(kb, name) >= 0.8
    )

    timeline = []
    for stage in kb.stages:
        reached = accumulated >= stage.gdd_start
        timeline.append(
            {
                "name": stage.name,
                "label": stage.label_pt,
                "gdd_start": stage.gdd_start,
                "kc": stage.kc,
                "water_sensitivity": stage.water_sensitivity,
                "reached": reached,
                "is_current": stage.name == current_stage.name,
                "started_on": stage_first_date.get(stage.name),
                "stats": per_stage.get(stage.name),
            }
        )

    return {
        "available": True,
        "crop_kb": kb.crop,
        "crop_label": kb.label_pt,
        "current_stage": current_stage.name,
        "current_stage_label": current_stage.label_pt,
        "current_kc": current_stage.kc,
        "current_water_sensitivity": current_stage.water_sensitivity,
        "accumulated_gdd": round(accumulated, 1),
        "cycle_gdd": kb.cycle_gdd,
        "cycle_progress_pct": round(cycle_progress * 100, 1),
        "days_since_planting": (obs[-1].date.date() - field.planting_date.date()).days,
        "critical_stage_heat_days": critical_heat_days,
        "timeline": timeline,
    }


def _stage_sensitivity(kb: CropKnowledge, stage_name: str) -> float:
    for stage in kb.stages:
        if stage.name == stage_name:
            return stage.water_sensitivity
    return 0.0
