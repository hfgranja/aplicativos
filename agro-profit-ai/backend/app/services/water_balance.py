"""Balanço hídrico agronômico baseado em FAO-56.

Substitui o proxy fixo de 4,5 mm/dia por:

1. Radiação extraterrestre Ra (FAO-56 eq. 21) a partir de latitude e dia
   do ano;
2. ET0 por Hargreaves-Samani (FAO-56 eq. 52): método recomendado quando só
   há temperatura — exatamente o mínimo garantido pelos nossos providers
   (ET0 = 0.0023 × (Tmean + 17.8) × √(Tmax − Tmin) × Ra, com Ra em mm/dia);
3. ETc = Kc × ET0, com Kc da fase fenológica corrente (crop_knowledge);
4. Balanço acumulado (chuva − ETc) por janela e índice de estresse hídrico
   ponderado pela sensibilidade da fase (déficit no florescimento pesa
   muito mais que no vegetativo).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app import models
from app.domain.crop_knowledge import get_crop_knowledge, stage_for_gdd
from app.services.phenology import daily_gdd

SOLAR_CONSTANT_MJ_M2_MIN = 0.0820
# Converte radiação MJ/m²/dia em lâmina equivalente de evaporação (mm/dia)
RADIATION_TO_MM = 0.408


def extraterrestrial_radiation_mm(lat_deg: float, day_of_year: int) -> float:
    """Ra (FAO-56 eq. 21) convertida para mm/dia de evaporação equivalente."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)
    delta = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
    ws_cos = -math.tan(phi) * math.tan(delta)
    ws = math.acos(min(1.0, max(-1.0, ws_cos)))
    ra_mj = (
        (24 * 60 / math.pi)
        * SOLAR_CONSTANT_MJ_M2_MIN
        * dr
        * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
    )
    return max(0.0, ra_mj * RADIATION_TO_MM)


def et0_hargreaves(t_min: float | None, t_max: float | None, lat_deg: float, day_of_year: int) -> float:
    """ET0 (mm/dia) por Hargreaves-Samani (FAO-56 eq. 52)."""
    if t_min is None or t_max is None or t_max < t_min:
        return 0.0
    t_mean = (t_min + t_max) / 2
    ra = extraterrestrial_radiation_mm(lat_deg, day_of_year)
    return max(0.0, 0.0023 * (t_mean + 17.8) * math.sqrt(t_max - t_min) * ra)


def compute_water_balance(db: Session, field: models.Field, window_days: int = 90) -> dict:
    """Série diária de ET0/ETc/balanço + índice de estresse hídrico.

    O Kc usado dia a dia é o da fase fenológica em que a cultura estava
    naquele dia (acúmulo real de GDD desde o plantio). Sem data de plantio,
    usa Kc médio de meio de ciclo (1.0) — sinalizado no retorno.
    """
    kb = get_crop_knowledge(field.crop)
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    start = field.planting_date if field.planting_date and field.planting_date > cutoff else cutoff

    obs = (
        db.query(models.WeatherObservation)
        .filter(
            models.WeatherObservation.field_id == field.id,
            models.WeatherObservation.kind == "observation",
            models.WeatherObservation.date >= start,
        )
        .order_by(models.WeatherObservation.date)
        .all()
    )
    if not obs or field.centroid_lat is None:
        return {"available": False}

    # GDD acumulado ANTES da janela (para saber a fase no início dela)
    accumulated_gdd = 0.0
    if field.planting_date and field.planting_date < start:
        prior = (
            db.query(models.WeatherObservation)
            .filter(
                models.WeatherObservation.field_id == field.id,
                models.WeatherObservation.kind == "observation",
                models.WeatherObservation.date >= field.planting_date,
                models.WeatherObservation.date < start,
            )
            .all()
        )
        for o in prior:
            accumulated_gdd += daily_gdd(o.temperature_min_c, o.temperature_max_c, kb)

    kc_from_phenology = bool(field.planting_date)
    series = []
    cumulative_balance = 0.0
    weighted_deficit = 0.0
    total_etc = 0.0
    stress_days = 0

    for o in obs:
        doy = o.date.timetuple().tm_yday
        et0 = et0_hargreaves(o.temperature_min_c, o.temperature_max_c, field.centroid_lat, doy)

        if kc_from_phenology:
            accumulated_gdd += daily_gdd(o.temperature_min_c, o.temperature_max_c, kb)
            stage = stage_for_gdd(kb, accumulated_gdd)
            kc, sensitivity = stage.kc, stage.water_sensitivity
        else:
            kc, sensitivity = 1.0, 0.6

        etc = kc * et0
        rain = o.precipitation_mm or 0.0
        daily_balance = rain - etc
        cumulative_balance += daily_balance
        total_etc += etc
        if daily_balance < 0:
            weighted_deficit += -daily_balance * sensitivity
            if etc > 0 and rain < etc * 0.4:
                stress_days += 1

        series.append(
            {
                "date": o.date.date().isoformat(),
                "rain_mm": round(rain, 1),
                "et0_mm": round(et0, 2),
                "etc_mm": round(etc, 2),
                "balance_mm": round(daily_balance, 2),
                "cumulative_balance_mm": round(cumulative_balance, 1),
            }
        )

    # Índice 0-100: déficit ponderado pela sensibilidade da fase, relativo à
    # demanda total do período. 0 = sem estresse; 100 = déficit severo em
    # fase crítica durante toda a janela.
    stress_index = min(100.0, (weighted_deficit / total_etc) * 100) if total_etc > 0 else 0.0

    return {
        "available": True,
        "kc_from_phenology": kc_from_phenology,
        "window_days": len(series),
        "total_rain_mm": round(sum(s["rain_mm"] for s in series), 1),
        "total_et0_mm": round(sum(s["et0_mm"] for s in series), 1),
        "total_etc_mm": round(total_etc, 1),
        "cumulative_balance_mm": round(cumulative_balance, 1),
        "water_stress_index": round(stress_index, 1),
        "stress_days": stress_days,
        "series": series,
    }
