# Agro Profit AI

Motor de decisão econômica geoespacial para agricultura — não um dashboard
de mapas, mas uma plataforma que responde onde agir, por quê, quanto custa,
quanto pode retornar e qual a confiança da recomendação. O KPI central é a
**margem de contribuição esperada por hectare**, não produtividade isolada.

Implementação da **Fase 1 / MVP** descrita na especificação funcional
completa (72 seções) fornecida para este projeto — cadastro de fazenda,
importação de talhões, clima (INMET → NASA POWER), solo (SoilGrids),
satélite (Copernicus Sentinel-2), benchmark regional (IBGE), upload de
produtividade/solo/operações do produtor, feature store, modelo de
produtividade (LightGBM champion vs. XGBoost challenger + quantile
regression), SHAP, motor econômico, motor de decisão e recomendações
priorizadas por valor econômico esperado.

## Onde está o quê

- [`docs/DESIGN.md`](docs/DESIGN.md) — decisões de implementação da Fase 1:
  o que é chamada real a fontes públicas, o que é fallback sintético
  claramente marcado, e o que fica para a Fase 2/3.
- [`backend/`](backend) — API (FastAPI + SQLAlchemy + SQLite, PostGIS-ready)
  com os providers (`app/providers/`), feature store (`app/services/
  feature_engineering.py`), pipeline de ML (`app/ml/`), motor econômico e
  motor de decisão (`app/services/`).
- [`frontend/`](frontend) — painel (React + Vite + Leaflet + Recharts) com
  visão executiva, mapa de rentabilidade/risco, detalhe de talhão (clima,
  satélite, solo, recomendações, simulador what-if com Monte Carlo),
  importação de dados e alertas.

## Rodando localmente

### Com Docker

```bash
cd agro-profit-ai
docker compose up
```

- Frontend: http://localhost:5173
- Backend/API: http://localhost:8000 (docs interativos em `/docs`)

### Sem Docker

```bash
# backend
cd agro-profit-ai/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data
uvicorn app.main:app --reload --port 8000

# frontend (em outro terminal)
cd agro-profit-ai/frontend
npm install
cp .env.example .env
npm run dev
```

Login de demonstração (semeado automaticamente no primeiro start):
**demo@agroprofit.ai / agro123** — uma fazenda com dois talhões (soja e
milho), uma safra de histórico e uma amostra de solo de laboratório já
carregadas.

## Providers de dados

Cada fonte da especificação vira um adapter atrás de uma interface comum
(`app/providers/base.py`) — trocar de fornecedor não exige tocar em
regras de negócio. Ver a tabela completa em
[`docs/DESIGN.md`](docs/DESIGN.md#2-providers--o-que-é-chamada-real-vs-o-que-é-placeholder-documentado).
Resumo: NASA POWER, INMET, Open-Meteo, SoilGrids e IBGE fazem chamadas HTTP
reais e sem chave; Copernicus Sentinel-2 tem o fluxo OAuth2 real implementado
(requer `COPERNICUS_CLIENT_ID`/`SECRET`); OpenWeather/Tomorrow.io/Planet são
opcionais e exigem chave própria do tenant; CHIRPS/ERA5-Land/MapBiomas/
Embrapa GeoInfo/Earth Engine têm a interface pronta mas a ingestão raster
real é Fase 2.

Sem nenhuma credencial configurada (ambiente de desenvolvimento típico), o
pipeline continua funcional ponta a ponta usando fallback sintético
claramente identificado (`is_synthetic` / `provider="synthetic_fallback"`) —
nunca apresentado como dado real na interface.

## O que está implementado vs. simulado vs. fora de escopo

| Implementado de verdade | Simulado / bootstrap (comportamento honesto, sem dado real) | Fora de escopo desta implementação (Fase 2/3) |
|---|---|---|
| Pipeline completo dado → feature → previsão → risco → economia → decisão → explicação | Modelo de produtividade treinado em prior sintético agronomicamente estruturado (`ml/training_data.py`) até existir histórico real suficiente | Modelos regionais/globais treinados em dados reais multi-fazenda |
| LightGBM vs. XGBoost (champion/challenger por MAE em holdout) + quantile P10/P50/P90 + SHAP | Anomalia via IsolationForest sobre a distribuição-prior (substituto do grid de células real) | `SpatialCell` populado automaticamente, CHIRPS/ERA5-Land/MapBiomas, IoT |
| Motor econômico (margem, ROI, break-even) + Monte Carlo (1000 simulações) | Risco por regras de limiar (não `LightGBMClassifier`, que exige outcomes rotulados) | Modelo de risco treinado, causal/uplift modeling, Copilot conversacional |
| Multi-tenancy com isolamento por `tenant_id` em toda tabela de domínio | Calibração simples por histórico do talhão (shrink em direção à média realizada) | Modelos verdadeiramente personalizados por fazenda, MLflow real |
| Providers reais sem chave (NASA POWER, INMET, SoilGrids, IBGE, Open-Meteo) | Fallback sintético determinístico quando provider indisponível/sem credencial | RBAC granular por endpoint (hoje: isolamento de tenant + `role` no token) |

## Princípio de produto

> Qual decisão aumenta a margem por hectare com melhor relação retorno-risco?

Essa é a pergunta que toda tela, todo endpoint e todo modelo deste
repositório existe para responder.
