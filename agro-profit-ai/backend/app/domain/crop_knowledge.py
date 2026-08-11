"""Base de conhecimento agronômico por cultura.

Parâmetros consolidados da literatura agronômica (FAO-56 para coeficientes
de cultura Kc e durações de fase; Embrapa/IAC para calagem por saturação de
bases, janelas de plantio e interpretação de análise de solo; literatura de
fenologia por graus-dia — ver docs/DESIGN.md "Referências agronômicas").

Estes são valores CONSERVADORES de referência, não prescrição: cultivares,
regiões e sistemas de manejo deslocam todos eles. O Agronomic Safety Layer
(spec seção 29) mantém toda recomendação derivada daqui como Decision
Support, sujeita a validação por responsável agronômico. Conforme o dataset
proprietário crescer (spec seção 64), estes priors devem ser recalibrados
por região/cultivar a partir de outcomes reais.

Estrutura de cada cultura:
- t_base_c / t_upper_c: temperaturas base/limite para acúmulo de graus-dia
- stages: fases fenológicas com limiar de GDD acumulado para INÍCIO da fase,
  Kc (FAO-56) da fase e sensibilidade a estresse hídrico (0-1, onde 1 =
  período crítico: déficit nessa fase custa produtividade de forma
  desproporcional — florescimento/enchimento de grãos)
- ph_ideal / target_base_saturation_pct: alvo de correção de acidez (método
  da saturação por bases: NC t/ha = (V2 - V1) × CTC / 100, PRNT 100%)
- p_critical_mg_dm3 / k_critical_cmolc_dm3: níveis críticos de P (Mehlich-1,
  solo argiloso) e K abaixo dos quais há resposta esperada à adubação
- heat_stress_c: temperatura máxima acima da qual há dano em fase crítica
- frost_risk_c: temperatura mínima com risco de dano
- planting_window: (mês_início, mês_fim) janela recomendada Brasil Central
- yield_potential_kg_ha: teto irrigado/sem estresse (potencial)
- yield_attainable_kg_ha: teto atingível em sequeiro bem manejado
- diseases: condições ambientais favoráveis às principais doenças
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PhenoStage:
    name: str
    label_pt: str
    gdd_start: float  # GDD acumulado em que a fase começa
    kc: float  # coeficiente de cultura FAO-56 da fase
    water_sensitivity: float  # 0-1; 1 = período crítico de déficit hídrico


@dataclass(frozen=True)
class DiseaseRisk:
    name: str
    label_pt: str
    t_min_c: float
    t_max_c: float
    rh_min_pct: float  # umidade relativa mínima (proxy de molhamento foliar)
    wet_days_in_window: int  # dias com chuva nos últimos 10 dias que favorecem
    stages: tuple[str, ...]  # fases em que a doença importa


@dataclass(frozen=True)
class CropKnowledge:
    crop: str
    label_pt: str
    cycle: str  # "annual" | "semi-perennial" | "perennial"
    t_base_c: float
    t_upper_c: float
    stages: tuple[PhenoStage, ...]
    cycle_gdd: float  # GDD total até maturidade fisiológica
    ph_ideal: tuple[float, float]
    target_base_saturation_pct: float
    p_critical_mg_dm3: float
    k_critical_cmolc_dm3: float
    heat_stress_c: float
    frost_risk_c: float
    planting_window: tuple[int, int]  # meses (1-12), Brasil Central
    yield_potential_kg_ha: float
    yield_attainable_kg_ha: float
    diseases: tuple[DiseaseRisk, ...] = field(default_factory=tuple)


SOJA = CropKnowledge(
    crop="soja",
    label_pt="Soja",
    cycle="annual",
    t_base_c=10.0,
    t_upper_c=30.0,
    stages=(
        PhenoStage("sowing", "Semeadura", 0, 0.40, 0.3),
        PhenoStage("emergence", "Emergência (VE)", 130, 0.40, 0.4),
        PhenoStage("vegetative", "Vegetativo (V2-Vn)", 300, 0.75, 0.4),
        PhenoStage("flowering", "Florescimento (R1-R2)", 750, 1.15, 1.0),
        PhenoStage("grain_filling", "Enchimento de grãos (R5)", 1050, 1.15, 1.0),
        PhenoStage("maturity", "Maturação (R7-R8)", 1500, 0.50, 0.2),
    ),
    cycle_gdd=1700,
    ph_ideal=(5.5, 6.5),
    target_base_saturation_pct=60.0,  # Embrapa/IAC: 60-63% para soja
    p_critical_mg_dm3=8.0,  # Mehlich-1, solo argiloso (>35% argila)
    k_critical_cmolc_dm3=0.15,
    heat_stress_c=33.0,
    frost_risk_c=2.0,
    planting_window=(10, 12),  # out-dez (respeitando vazio sanitário)
    yield_potential_kg_ha=6000,
    yield_attainable_kg_ha=4200,
    diseases=(
        DiseaseRisk(
            name="asian_rust",
            label_pt="Ferrugem-asiática (Phakopsora pachyrhizi)",
            t_min_c=18.0,
            t_max_c=26.5,
            rh_min_pct=80.0,
            wet_days_in_window=4,
            stages=("flowering", "grain_filling"),
        ),
        DiseaseRisk(
            name="white_mold",
            label_pt="Mofo-branco (Sclerotinia sclerotiorum)",
            t_min_c=15.0,
            t_max_c=25.0,
            rh_min_pct=85.0,
            wet_days_in_window=5,
            stages=("flowering",),
        ),
    ),
)

MILHO = CropKnowledge(
    crop="milho",
    label_pt="Milho",
    cycle="annual",
    t_base_c=10.0,
    t_upper_c=34.0,
    stages=(
        PhenoStage("sowing", "Semeadura", 0, 0.40, 0.3),
        PhenoStage("emergence", "Emergência (VE)", 120, 0.40, 0.4),
        PhenoStage("vegetative", "Vegetativo (V2-Vn)", 300, 0.80, 0.5),
        PhenoStage("flowering", "Pendoamento/Espigamento (VT-R1)", 900, 1.20, 1.0),
        PhenoStage("grain_filling", "Enchimento de grãos (R2-R5)", 1200, 1.20, 0.9),
        PhenoStage("maturity", "Maturação (R6)", 1750, 0.60, 0.2),
    ),
    cycle_gdd=1950,
    ph_ideal=(5.5, 6.5),
    target_base_saturation_pct=60.0,
    p_critical_mg_dm3=8.0,
    k_critical_cmolc_dm3=0.15,
    heat_stress_c=35.0,
    frost_risk_c=2.0,
    planting_window=(9, 12),  # safra verão; safrinha jan-mar tratada à parte
    yield_potential_kg_ha=14000,
    yield_attainable_kg_ha=9500,
    diseases=(
        DiseaseRisk(
            name="corn_leaf_blight",
            label_pt="Helmintosporiose (Exserohilum turcicum)",
            t_min_c=18.0,
            t_max_c=27.0,
            rh_min_pct=85.0,
            wet_days_in_window=4,
            stages=("vegetative", "flowering"),
        ),
    ),
)

ALGODAO = CropKnowledge(
    crop="algodao",
    label_pt="Algodão",
    cycle="annual",
    t_base_c=12.0,
    t_upper_c=35.0,
    stages=(
        PhenoStage("sowing", "Semeadura", 0, 0.35, 0.3),
        PhenoStage("emergence", "Emergência", 150, 0.35, 0.4),
        PhenoStage("vegetative", "Vegetativo (B1)", 450, 0.75, 0.5),
        PhenoStage("flowering", "Florescimento (F1)", 900, 1.18, 1.0),
        PhenoStage("grain_filling", "Formação de capulhos (C1)", 1400, 1.10, 0.8),
        PhenoStage("maturity", "Maturação/abertura", 2000, 0.60, 0.2),
    ),
    cycle_gdd=2300,
    ph_ideal=(5.8, 6.5),
    target_base_saturation_pct=65.0,
    p_critical_mg_dm3=10.0,
    k_critical_cmolc_dm3=0.18,
    heat_stress_c=36.0,
    frost_risk_c=5.0,
    planting_window=(11, 1),
    yield_potential_kg_ha=6500,
    yield_attainable_kg_ha=4500,
)

FEIJAO = CropKnowledge(
    crop="feijao",
    label_pt="Feijão",
    cycle="annual",
    t_base_c=10.0,
    t_upper_c=30.0,
    stages=(
        PhenoStage("sowing", "Semeadura", 0, 0.40, 0.3),
        PhenoStage("emergence", "Emergência (V1)", 110, 0.40, 0.4),
        PhenoStage("vegetative", "Vegetativo (V3-V4)", 280, 0.75, 0.5),
        PhenoStage("flowering", "Florescimento (R6)", 550, 1.15, 1.0),
        PhenoStage("grain_filling", "Enchimento de vagens (R8)", 800, 1.10, 0.9),
        PhenoStage("maturity", "Maturação (R9)", 1050, 0.35, 0.2),
    ),
    cycle_gdd=1200,
    ph_ideal=(5.5, 6.5),
    target_base_saturation_pct=70.0,
    p_critical_mg_dm3=10.0,
    k_critical_cmolc_dm3=0.15,
    heat_stress_c=32.0,
    frost_risk_c=2.0,
    planting_window=(10, 2),
    yield_potential_kg_ha=4000,
    yield_attainable_kg_ha=2500,
)

TRIGO = CropKnowledge(
    crop="trigo",
    label_pt="Trigo",
    cycle="annual",
    t_base_c=4.0,
    t_upper_c=26.0,
    stages=(
        PhenoStage("sowing", "Semeadura", 0, 0.30, 0.3),
        PhenoStage("emergence", "Emergência", 120, 0.30, 0.4),
        PhenoStage("vegetative", "Perfilhamento/alongamento", 400, 0.80, 0.5),
        PhenoStage("flowering", "Espigamento/antese", 900, 1.15, 1.0),
        PhenoStage("grain_filling", "Enchimento de grãos", 1200, 1.10, 0.9),
        PhenoStage("maturity", "Maturação", 1550, 0.40, 0.2),
    ),
    cycle_gdd=1700,
    ph_ideal=(5.5, 6.5),
    target_base_saturation_pct=60.0,
    p_critical_mg_dm3=10.0,
    k_critical_cmolc_dm3=0.15,
    heat_stress_c=30.0,
    frost_risk_c=-2.0,  # tolera geada leve fora do espigamento
    planting_window=(4, 6),
    yield_potential_kg_ha=6500,
    yield_attainable_kg_ha=3500,
)

CANA = CropKnowledge(
    crop="cana_de_acucar",
    label_pt="Cana-de-açúcar",
    cycle="semi-perennial",
    t_base_c=16.0,
    t_upper_c=38.0,
    stages=(
        PhenoStage("sowing", "Plantio/brotação", 0, 0.40, 0.4),
        PhenoStage("vegetative", "Perfilhamento", 600, 0.80, 0.6),
        PhenoStage("grain_filling", "Crescimento de colmos", 1500, 1.25, 0.9),
        PhenoStage("maturity", "Maturação", 3800, 0.75, 0.2),
    ),
    cycle_gdd=4500,
    ph_ideal=(5.5, 6.5),
    target_base_saturation_pct=60.0,
    p_critical_mg_dm3=10.0,
    k_critical_cmolc_dm3=0.18,
    heat_stress_c=38.0,
    frost_risk_c=2.0,
    planting_window=(1, 4),
    yield_potential_kg_ha=140000,
    yield_attainable_kg_ha=85000,
)

CAFE = CropKnowledge(
    crop="cafe",
    label_pt="Café",
    cycle="perennial",
    t_base_c=10.0,
    t_upper_c=32.0,
    stages=(
        PhenoStage("vegetative", "Vegetativo/pós-colheita", 0, 0.90, 0.5),
        PhenoStage("flowering", "Florada", 800, 1.05, 1.0),
        PhenoStage("grain_filling", "Granação", 1600, 1.10, 0.9),
        PhenoStage("maturity", "Maturação/colheita", 2800, 0.95, 0.3),
    ),
    cycle_gdd=3200,
    ph_ideal=(5.0, 6.0),
    target_base_saturation_pct=60.0,
    p_critical_mg_dm3=10.0,
    k_critical_cmolc_dm3=0.20,
    heat_stress_c=34.0,
    frost_risk_c=1.0,
    planting_window=(11, 2),
    yield_potential_kg_ha=4800,  # café beneficiado
    yield_attainable_kg_ha=2400,
)

CROP_KB: dict[str, CropKnowledge] = {
    "soja": SOJA,
    "milho": MILHO,
    "algodao": ALGODAO,
    "feijao": FEIJAO,
    "trigo": TRIGO,
    "cana_de_acucar": CANA,
    "cafe": CAFE,
}


def get_crop_knowledge(crop: str | None) -> CropKnowledge:
    """Cultura não mapeada cai no perfil da soja (cultura anual C3 genérica)
    — sempre com o rótulo original preservado pelo chamador."""
    if not crop:
        return SOJA
    return CROP_KB.get(crop.lower().strip(), SOJA)


def stage_for_gdd(kb: CropKnowledge, accumulated_gdd: float) -> PhenoStage:
    current = kb.stages[0]
    for stage in kb.stages:
        if accumulated_gdd >= stage.gdd_start:
            current = stage
        else:
            break
    return current
