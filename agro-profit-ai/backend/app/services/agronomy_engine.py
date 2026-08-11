"""Motor agronômico — o "o que fazer" com dose calculada.

Evolui o Decision Engine de limiares genéricos para regras agronômicas
consolidadas, cada uma produzindo uma intervenção candidata com dose,
custo estimado e resposta esperada de produtividade. O Decision Engine
continua responsável por precificar cada candidata (Economic Engine +
Monte Carlo) e classificar ACTION/MONITOR/DO_NOT_ACT — este módulo só
produz o diagnóstico e a prescrição técnica.

Regras implementadas (referências em docs/DESIGN.md):

1. CALAGEM — método da saturação por bases (Embrapa/IAC):
   NC (t/ha, PRNT 100%) = (V2 − V1) × CTC / 100
   onde V2 = saturação-alvo da cultura (soja/milho 60%, feijão 70%...),
   V1 = saturação atual, CTC em cmolc/dm³ (camada 0-20 cm).
2. FOSFATAGEM CORRETIVA — quando P (Mehlich-1) < nível crítico da cultura
   em solo argiloso: ~15 kg P2O5/ha por mg/dm³ de déficit (Sousa & Lobato,
   Cerrado), limitado a 150 kg/ha por safra.
3. POTÁSSIO — quando K < nível crítico: 50-100 kg K2O/ha.
4. NITROGÊNIO EM COBERTURA — milho/trigo em fase vegetativa (soja não:
   fixação biológica dispensa N mineral).
5. IRRIGAÇÃO SUPLEMENTAR — dimensionada pelo déficit do balanço hídrico
   FAO-56, com prioridade máxima quando a fase atual é crítica
   (florescimento/enchimento).
6. RISCO DE DOENÇA — condições ambientais favoráveis (temperatura + UR +
   dias de chuva) cruzadas com a fase suscetível (ex.: ferrugem-asiática
   da soja, perdas de até 90% sem controle — Embrapa Soja).
7. ESTRESSE TÉRMICO EM FASE CRÍTICA e RISCO DE GEADA (usa previsão quando
   houver provider de forecast configurado).
8. JANELA DE PLANTIO — alerta quando o plantio ocorreu/ocorreria fora da
   janela recomendada regional.

Todas as saídas são Decision Support (spec seção 29): exibidas sempre com
o aviso de validação por responsável agronômico.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import datetime

from app.domain.crop_knowledge import CropKnowledge, get_crop_knowledge

# Custos de referência (R$, ordem de grandeza Brasil 2025/26) — configuráveis
# por tenant no futuro; usados apenas para ranking econômico inicial.
COST_LIME_PER_TON = 160.0  # calcário aplicado (produto + frete + aplicação)
COST_P2O5_PER_KG = 5.0
COST_K2O_PER_KG = 4.5
COST_N_PER_KG = 5.0
COST_FUNGICIDE_APPLICATION = 220.0  # produto + operação, por aplicação
COST_IRRIGATION_PER_MM = 4.0
COST_SCOUTING = 25.0


@dataclass
class AgronomicAction:
    category: str  # liming | phosphorus | potassium | nitrogen | irrigation | disease | heat | frost | planting_window | scouting
    priority: str  # high | medium | low
    issue: str
    evidence: list[str]
    action_label: str
    dose_description: str
    cost_per_ha: float
    response_pct: float  # resposta esperada de produtividade (fração, ex.: 0.08)
    stage_context: str = ""


def evaluate(
    features: dict,
    phenology: dict,
    water_balance: dict,
    forecast_rows: list[dict] | None = None,
    crop: str | None = None,
    planting_date: datetime | None = None,
) -> list[AgronomicAction]:
    kb = get_crop_knowledge(crop)
    actions: list[AgronomicAction] = []

    actions += _liming(features, kb)
    actions += _phosphorus(features, kb)
    actions += _potassium(features, kb)
    actions += _nitrogen_topdress(features, phenology, kb)
    actions += _irrigation(features, phenology, water_balance, kb)
    actions += _disease_risk(features, phenology, kb)
    actions += _heat_and_frost(features, phenology, forecast_rows, kb)
    actions += _planting_window(planting_date, kb)
    actions += _vigor_anomaly(features, phenology)

    return actions


# ---------------------------------------------------------------- regras


def _liming(features: dict, kb: CropKnowledge) -> list[AgronomicAction]:
    v1 = features.get("soil_base_saturation")
    cec = features.get("soil_cec")
    ph = features.get("soil_ph")

    # Sem V% e CTC não há como calcular dose — cai para o sinal simples de pH.
    if v1 is not None and cec is not None:
        v2 = kb.target_base_saturation_pct
        if v1 < v2 - 5:  # margem de 5 pontos para não recomendar micro-correções
            nc_t_ha = round((v2 - v1) * cec / 100, 1)
            nc_t_ha = min(nc_t_ha, 6.0)  # limite prático por aplicação
            gap = v2 - v1
            response = min(0.12, 0.004 * gap)  # até 12% com gap de 30 pontos
            return [
                AgronomicAction(
                    category="liming",
                    priority="high" if gap > 15 else "medium",
                    issue=f"Saturação por bases ({v1:.0f}%) abaixo do alvo de {v2:.0f}% para {kb.label_pt}",
                    evidence=[
                        f"V% atual: {v1:.0f}% · alvo: {v2:.0f}%",
                        f"CTC: {cec} cmolc/dm³",
                        f"NC = (V2−V1)×CTC/100 = {nc_t_ha} t/ha (PRNT 100%)",
                    ],
                    action_label="Calagem para correção da acidez",
                    dose_description=f"{nc_t_ha} t/ha de calcário (corrigir pelo PRNT real do produto), incorporado 0-20 cm",
                    cost_per_ha=round(nc_t_ha * COST_LIME_PER_TON, 0),
                    response_pct=response,
                )
            ]
    if ph is not None and ph < kb.ph_ideal[0] - 0.3:
        return [
            AgronomicAction(
                category="liming",
                priority="medium",
                issue=f"pH do solo ({ph}) abaixo da faixa ideal {kb.ph_ideal[0]}-{kb.ph_ideal[1]} para {kb.label_pt}",
                evidence=[f"pH: {ph}", "Sem V%/CTC na amostra para calcular dose — coletar análise completa"],
                action_label="Calagem (dose a definir com análise completa)",
                dose_description="Coletar análise com V% e CTC para dimensionar via saturação por bases",
                cost_per_ha=350.0,
                response_pct=0.06,
            )
        ]
    return []


def _phosphorus(features: dict, kb: CropKnowledge) -> list[AgronomicAction]:
    p = features.get("soil_phosphorus")
    if p is None or p >= kb.p_critical_mg_dm3:
        return []
    deficit = kb.p_critical_mg_dm3 - p
    dose_p2o5 = min(150.0, round(deficit * 15, 0))  # Sousa & Lobato, solo argiloso
    severity = deficit / kb.p_critical_mg_dm3
    return [
        AgronomicAction(
            category="phosphorus",
            priority="high" if severity > 0.5 else "medium",
            issue=f"Fósforo ({p} mg/dm³) abaixo do nível crítico ({kb.p_critical_mg_dm3} mg/dm³) para {kb.label_pt}",
            evidence=[
                f"P Mehlich-1: {p} mg/dm³ · crítico: {kb.p_critical_mg_dm3} mg/dm³",
                f"Déficit: {deficit:.1f} mg/dm³ → ~15 kg P2O5/ha por mg/dm³",
            ],
            action_label="Fosfatagem corretiva",
            dose_description=f"{dose_p2o5:.0f} kg P2O5/ha a lanço incorporado (ou no sulco na próxima semeadura)",
            cost_per_ha=round(dose_p2o5 * COST_P2O5_PER_KG, 0),
            response_pct=min(0.10, 0.10 * severity + 0.03),
        )
    ]


def _potassium(features: dict, kb: CropKnowledge) -> list[AgronomicAction]:
    k = features.get("soil_potassium")
    if k is None or k >= kb.k_critical_cmolc_dm3:
        return []
    dose_k2o = 80.0 if k < kb.k_critical_cmolc_dm3 * 0.6 else 50.0
    return [
        AgronomicAction(
            category="potassium",
            priority="medium",
            issue=f"Potássio ({k} cmolc/dm³) abaixo do nível crítico ({kb.k_critical_cmolc_dm3}) para {kb.label_pt}",
            evidence=[f"K trocável: {k} cmolc/dm³ · crítico: {kb.k_critical_cmolc_dm3} cmolc/dm³"],
            action_label="Adubação potássica",
            dose_description=f"{dose_k2o:.0f} kg K2O/ha (KCl), parcelado se solo arenoso",
            cost_per_ha=round(dose_k2o * COST_K2O_PER_KG, 0),
            response_pct=0.06,
        )
    ]


def _nitrogen_topdress(features: dict, phenology: dict, kb: CropKnowledge) -> list[AgronomicAction]:
    # Soja e feijão bem nodulado dispensam N mineral (fixação biológica).
    if kb.crop in ("soja", "feijao"):
        return []
    if not phenology.get("available") or phenology.get("current_stage") != "vegetative":
        return []
    om = features.get("soil_organic_matter")
    dose_n = 120.0 if (om is not None and om < 20) else 90.0
    return [
        AgronomicAction(
            category="nitrogen",
            priority="high",
            issue=f"{kb.label_pt} em fase vegetativa — janela de N em cobertura aberta",
            evidence=[
                f"Fase atual: {phenology.get('current_stage_label')}",
                f"Matéria orgânica: {om} g/kg" if om is not None else "Matéria orgânica não informada",
            ],
            action_label="Nitrogênio em cobertura",
            dose_description=f"{dose_n:.0f} kg N/ha (ureia ou fontes estabilizadas), aplicar com solo úmido",
            cost_per_ha=round(dose_n * COST_N_PER_KG, 0),
            response_pct=0.12 if dose_n >= 120 else 0.09,
            stage_context="vegetative",
        )
    ]


def _irrigation(features: dict, phenology: dict, water_balance: dict, kb: CropKnowledge) -> list[AgronomicAction]:
    if not water_balance.get("available"):
        # fallback para o sinal simples de dias secos
        dry = features.get("consecutive_dry_days")
        if dry is not None and dry >= 10:
            return [
                AgronomicAction(
                    category="irrigation",
                    priority="high",
                    issue="Sequência prolongada sem chuva",
                    evidence=[f"Dias consecutivos sem chuva: {dry}"],
                    action_label="Irrigação suplementar",
                    dose_description="~30 mm de lâmina, reavaliar após próxima chuva",
                    cost_per_ha=round(30 * COST_IRRIGATION_PER_MM, 0),
                    response_pct=0.10,
                )
            ]
        return []

    stress = water_balance.get("water_stress_index", 0)
    deficit = -min(0.0, water_balance.get("cumulative_balance_mm", 0))
    if stress < 15 or deficit < 20:
        return []

    in_critical_stage = phenology.get("available") and phenology.get("current_water_sensitivity", 0) >= 0.8
    # Lâmina: repor até 60% do déficit acumulado, limitada a 60 mm por ciclo de recomendação
    lamina = min(60.0, round(deficit * 0.6, 0))
    response = min(0.20, stress / 100 * (1.6 if in_critical_stage else 0.8))
    return [
        AgronomicAction(
            category="irrigation",
            priority="high" if in_critical_stage else "medium",
            issue=(
                f"Déficit hídrico ({deficit:.0f} mm acumulado) "
                + ("durante fase crítica " + phenology.get("current_stage_label", "") if in_critical_stage else "no período recente")
            ),
            evidence=[
                f"Índice de estresse hídrico (FAO-56): {stress}",
                f"Balanço acumulado (chuva − ETc): {water_balance['cumulative_balance_mm']} mm",
                f"ETc do período: {water_balance['total_etc_mm']} mm · chuva: {water_balance['total_rain_mm']} mm",
            ]
            + ([f"Fase atual: {phenology.get('current_stage_label')} (sensibilidade {phenology.get('current_water_sensitivity')})"] if phenology.get("available") else []),
            action_label="Irrigação suplementar dimensionada pelo balanço hídrico",
            dose_description=f"Lâmina de {lamina:.0f} mm, fracionada em 2-3 aplicações",
            cost_per_ha=round(lamina * COST_IRRIGATION_PER_MM, 0),
            response_pct=response,
            stage_context=phenology.get("current_stage", ""),
        )
    ]


def _disease_risk(features: dict, phenology: dict, kb: CropKnowledge) -> list[AgronomicAction]:
    if not phenology.get("available"):
        return []
    stage = phenology.get("current_stage")
    t_mean = features.get("temperature_mean_30d")
    rh = features.get("relative_humidity_30d")
    rain_10d = features.get("rain_7d", 0) + (features.get("rain_15d", 0) - features.get("rain_7d", 0)) * 0.4

    actions = []
    for disease in kb.diseases:
        if stage not in disease.stages:
            continue
        if t_mean is None or rh is None:
            continue
        favorable_temp = disease.t_min_c <= t_mean <= disease.t_max_c
        favorable_humidity = rh >= disease.rh_min_pct - 5
        wet_enough = rain_10d >= disease.wet_days_in_window * 4  # proxy: mm em vez de contagem
        score = sum([favorable_temp, favorable_humidity, wet_enough])
        if score >= 2:
            actions.append(
                AgronomicAction(
                    category="disease",
                    priority="high" if score == 3 else "medium",
                    issue=f"Condições favoráveis a {disease.label_pt} em fase suscetível",
                    evidence=[
                        f"Fase: {phenology.get('current_stage_label')} (suscetível)",
                        f"Temperatura média 30d: {t_mean}°C (favorável: {disease.t_min_c}-{disease.t_max_c}°C)",
                        f"UR média 30d: {rh}% (favorável: ≥{disease.rh_min_pct}%)",
                        f"Chuva recente: {rain_10d:.0f} mm/10d",
                    ],
                    action_label=f"Monitoramento intensivo + avaliar controle de {disease.label_pt.split('(')[0].strip()}",
                    dose_description="Vistoria em 48h; se detectado, aplicação de fungicida conforme bula e rotação de mecanismos de ação",
                    cost_per_ha=COST_FUNGICIDE_APPLICATION if score == 3 else COST_SCOUTING,
                    # Valor esperado modelado como perda evitada conservadora,
                    # não o teto de dano da doença (ferrugem chega a 90%).
                    response_pct=0.12 if score == 3 else 0.04,
                    stage_context=stage,
                )
            )
    return actions


def _heat_and_frost(
    features: dict, phenology: dict, forecast_rows: list[dict] | None, kb: CropKnowledge
) -> list[AgronomicAction]:
    actions = []
    if phenology.get("available") and phenology.get("critical_stage_heat_days", 0) >= 3:
        actions.append(
            AgronomicAction(
                category="heat",
                priority="medium",
                issue=f"Estresse térmico recorrente (≥{kb.heat_stress_c}°C) em fase crítica",
                evidence=[f"Dias de calor extremo em fase crítica: {phenology['critical_stage_heat_days']}"],
                action_label="Mitigação de estresse térmico",
                dose_description="Se irrigado: irrigar no início da tarde nos picos; registrar impacto para seleção de cultivar mais tolerante na próxima safra",
                cost_per_ha=COST_IRRIGATION_PER_MM * 10,
                response_pct=0.04,
            )
        )
    if forecast_rows:
        frost_days = [r for r in forecast_rows if (r.get("temperature_min_c") or 99) <= kb.frost_risk_c]
        if frost_days:
            actions.append(
                AgronomicAction(
                    category="frost",
                    priority="high",
                    issue=f"Risco de geada na previsão ({len(frost_days)} dia(s) com mínima ≤ {kb.frost_risk_c}°C)",
                    evidence=[f"{r['date']}: mínima prevista {r.get('temperature_min_c')}°C" for r in frost_days[:3]],
                    action_label="Plano de contingência para geada",
                    dose_description="Se irrigado: irrigação na madrugada do evento; antecipar colheita se maturação próxima",
                    cost_per_ha=50.0,
                    response_pct=0.05,
                )
            )
    return actions


def _planting_window(planting_date: datetime | None, kb: CropKnowledge) -> list[AgronomicAction]:
    if not planting_date:
        return []
    month = planting_date.month
    start, end = kb.planting_window
    inside = (start <= month <= end) if start <= end else (month >= start or month <= end)
    if inside:
        return []
    return [
        AgronomicAction(
            category="planting_window",
            priority="low",
            issue=f"Plantio registrado fora da janela recomendada para {kb.label_pt} (meses {start}-{end})",
            evidence=[f"Data de plantio: {planting_date.date().isoformat()}"],
            action_label="Planejamento da próxima safra",
            dose_description="Programar semeadura dentro da janela recomendada; plantio fora de época amplia risco climático e de doenças",
            cost_per_ha=0.0,
            response_pct=0.05,  # ganho estimado ao voltar para a janela na próxima safra
        )
    ]


def _vigor_anomaly(features: dict, phenology: dict) -> list[AgronomicAction]:
    ndvi_current = features.get("ndvi_current")
    ndvi_mean = features.get("ndvi_mean_30d")
    if ndvi_current is None or ndvi_mean in (None, 0):
        return []
    drop = (ndvi_mean - ndvi_current) / ndvi_mean
    if drop <= 0.12:
        return []
    return [
        AgronomicAction(
            category="scouting",
            priority="high" if drop > 0.2 else "medium",
            issue=f"Queda de vigor (NDVI) de {drop * 100:.0f}% vs. média de 30 dias",
            evidence=[
                f"NDVI atual: {ndvi_current} · média 30d: {round(ndvi_mean, 3)}",
                "Causas possíveis: praga, doença, déficit nutricional ou hídrico localizado",
            ],
            action_label="Vistoria de campo dirigida",
            dose_description="Inspecionar as zonas de menor NDVI em 48h; coletar amostras foliares se padrão nutricional",
            cost_per_ha=COST_SCOUTING,
            response_pct=0.05,
        )
    ]
