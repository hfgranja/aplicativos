"""IBGE — Produção Agrícola Municipal (PAM), benchmark regional (spec 4.12).

API pública SIDRA, sem autenticação. Tabela 1612 (PAM) — variável 214 é o
rendimento médio (kg/ha). Nunca usar como ground truth de talhão — apenas
como prior de cold start / baseline regional / detecção de anomalia (spec
4.12 e seção 44).
"""
from __future__ import annotations

from app.providers.base import ProviderUnavailableError, RegionalBenchmarkProvider
from app.providers.http_client import get_json

SIDRA_BASE = "https://apisidra.ibge.gov.br/values"
PAM_TABLE = 1612

# SIDRA product codes (classificação 81 - produtos das lavouras) for common
# row crops. Extend as needed; unmapped crops fall back to ProviderUnavailableError.
CROP_CODES = {
    "soja": 2713,
    "milho": 2711,
    "algodao": 2696,
    "cafe": 2700,
    "cana_de_acucar": 2717,
    "feijao": 2706,
    "trigo": 2722,
}

# variable 109 = área plantada (ha), 112 = produção (t), 214 = rendimento médio (kg/ha)
VARIABLES = "109,112,214"


class IbgeProvider(RegionalBenchmarkProvider):
    name = "ibge_pam"

    def municipal_yield(self, crop: str, ibge_municipality_code: str, year: int) -> dict:
        product_code = CROP_CODES.get(crop.lower().strip())
        if product_code is None:
            raise ProviderUnavailableError(f"ibge_pam: unmapped crop '{crop}' — extend CROP_CODES")

        url = f"{SIDRA_BASE}/t/{PAM_TABLE}/n6/{ibge_municipality_code}/v/{VARIABLES}/p/{year}/c81/{product_code}"
        rows = get_json(url)
        # SIDRA always returns a header row at index 0 with the field codes.
        data_rows = [r for r in rows if r.get("NC") == "Município"] if rows else []
        if not data_rows:
            raise ProviderUnavailableError("ibge_pam: no data rows for given municipality/crop/year")

        result: dict[str, float] = {}
        for r in data_rows:
            var_name = r.get("D3N", "")
            try:
                value = float(r.get("V", "").replace(",", "."))
            except (ValueError, AttributeError):
                continue
            if "Área plantada" in var_name:
                result["harvested_area_ha"] = value
            elif "Rendimento médio" in var_name:
                result["average_yield_kg_ha"] = value
            elif "Quantidade produzida" in var_name:
                result["production_t"] = value

        if "average_yield_kg_ha" not in result:
            raise ProviderUnavailableError("ibge_pam: response missing rendimento médio")

        result.update({"crop": crop, "municipality_code": ibge_municipality_code, "year": year, "source": self.name})
        return result
