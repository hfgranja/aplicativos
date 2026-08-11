# Agro Profit AI — Notas de implementação (Fase 1 / MVP)

Este documento não repete a especificação funcional completa (72 seções,
fornecida pelo usuário) — ele registra **como a Fase 1 (spec seção 59) foi
implementada**, quais decisões de engenharia foram tomadas dentro do escopo
do MVP, e o que fica explicitamente para a Fase 2/3 (seções 60-63).

A pergunta que guia todo o produto continua sendo a da spec seção 72:

> Qual decisão aumenta a margem por hectare com melhor relação retorno-risco?

## 1. Arquitetura implementada

```
DATA SOURCES (providers/) → INGESTION (services/ingestion.py) →
FEATURE STORE (services/feature_engineering.py) → ML PREDICTION (ml/) →
RISK (services/decision_engine.detect_risk_signals) →
ECONOMIC ENGINE (services/economic_engine.py, monte_carlo.py) →
DECISION ENGINE (services/decision_engine.py) → RECOMMENDATION →
EXPLAINABILITY (ml/explainability.py) → API (routers/) → UI (frontend/)
```

Isso segue literalmente o pipeline da spec seção 70. Cada camada só conhece
a camada imediatamente abaixo — nenhum router chama um provider diretamente,
nenhum provider é referenciado fora de `app/providers/`.

Hierarquia geoespacial (spec seção 1/8): `Tenant → Farm → Field →
ManagementZone → SpatialCell`, todos modelados em `app/models.py`. O grid de
`SpatialCell` existe no schema mas a Fase 1 não popula automaticamente um
grid 10/20/30/50/100m por talhão — isso é trabalho de ingestão de imagem
raster zonal (Fase 2, junto com CHIRPS/ERA5/MapBiomas).

## 2. Providers — o que é chamada real vs. o que é placeholder documentado

Todo provider implementa uma interface em `app/providers/base.py`
(`WeatherProvider`, `SatelliteProvider`, `SoilProvider`,
`MarketPriceProvider`, `FarmDataProvider`, `RegionalBenchmarkProvider`) e é
orquestrado por um `ProviderRouter` com fallback (spec seção 52).

| Provider | Status | Nota |
|---|---|---|
| NASA POWER | Chamada HTTP real, sem autenticação | `providers/weather/nasa_power_provider.py` |
| INMET (apitempo) | Chamada HTTP real, best-effort (API pública não versionada) | `providers/weather/inmet_provider.py` |
| Open-Meteo | Chamada HTTP real, licenciamento não comercial (`ALLOW_NON_COMMERCIAL_PROVIDERS`) | `providers/weather/openmeteo_provider.py` |
| OpenWeather / Tomorrow.io | Chamada HTTP real, requer API key própria do tenant | desabilitado por padrão |
| SoilGrids/ISRIC | Chamada HTTP real, sem autenticação | `providers/soil/soilgrids_provider.py` |
| IBGE (SIDRA/PAM) | Chamada HTTP real, sem autenticação | `providers/agriculture/ibge_provider.py` — usado só como benchmark, nunca como ground truth |
| Copernicus Sentinel-2 | Fluxo OAuth2 real implementado; sem credenciais configuradas, cai em gerador sintético determinístico marcado `is_synthetic=True` | `providers/satellite/copernicus_provider.py` |
| CHIRPS, ERA5-Land, MapBiomas, Embrapa GeoInfo, Earth Engine, Planet | Interface implementada, chamada real **não** implementada (rasters/OAuth/billing próprios) — Fase 2, seção 60 | levantam `ProviderUnavailableError` com o motivo |

**Por que isso importa:** o ambiente de desenvolvimento/CI deste repositório
não tem acesso de saída à internet pública. Em vez de mockar tudo, cada
provider faz uma tentativa de chamada real e, só quando ela falha
(indisponibilidade, sem credenciais, sem rede), o pipeline cai em dados
sintéticos claramente identificados (`provider="synthetic_fallback"` /
`is_synthetic=True`). Isso mantém o produto exercitável ponta a ponta em
qualquer ambiente sem nunca apresentar dado sintético como observação real
— e em produção, com rede liberada e credenciais configuradas, os mesmos
adapters passam a usar dados reais sem nenhuma mudança de código.

## 3. Machine Learning — bootstrap honesto, não um modelo fingido

A spec (seção 16-20, 44, 64) é explícita: cold start deve usar prior
regional + confiança baixa, e o verdadeiro moat é o dataset proprietário
acumulado safra a safra. Como este MVP não tem (ainda) um dataset real
multi-fazenda rotulado, `ml/training_data.py` gera um **prior sintético
documentado**: features em faixas fisicamente plausíveis, combinadas por
uma função de resposta agronômica (adequação hídrica, acúmulo térmico,
vigor por NDVI, pH, fertilidade), ancorada em ordens de grandeza do IBGE
PAM por cultura. Isso é declarado explicitamente no código e deve ser
substituído por um modelo regional/global treinado em dados reais assim que
houver volume suficiente (spec seção 43, hierarquia de modelos).

Sobre esse prior:

- **Champion vs Challenger real** (spec seção 17-18): LightGBM e XGBoost são
  treinados e comparados por MAE em holdout; o menor MAE vira champion
  (`ml/model_registry.py`).
- **Quantile regression P10/P50/P90** (spec seção 20): três LightGBM com
  `objective="quantile"`.
- **SHAP** (spec seção 23): `shap.TreeExplainer` sobre o modelo champion,
  traduzido para rótulos em PT-BR.
- **Anomalia** (spec seção 21): IsolationForest treinado na mesma
  distribuição-prior + regra de queda de NDVI vs. média móvel — substituto
  de MVP para a comparação célula-vs-célula/histórico que exige um grid de
  `SpatialCell` populado (Fase 2/3).
- **Calibração por histórico**: quando o talhão já tem `YieldRecord`
  próprios, a previsão do modelo global é encolhida (`_calibrate_with_history`
  em `ml/yield_model.py`) em direção à média realizada do talhão — uma ponte
  simples para os modelos personalizados por fazenda da Fase 3 (seção 43),
  sem implementar retraining completo por tenant.
- **Risco** (spec seção 22): regras de limiar sobre features (pH, NDVI vs
  média, dias secos, balanço hídrico) em vez de um `LightGBMClassifier`
  treinado — a spec já reconhece que os targets de risco são "futuros",
  dependentes de outcomes rotulados que só existem depois de safras reais
  monitoradas.

## 4. Confidence Engine (spec seção 44-45)

`services/confidence_engine.py` computa 0-100 a partir de: proveniência do
clima (estação real vs. NASA POWER vs. sintético), frescor/quantidade de
cenas de satélite, origem do solo (laboratório > SoilGrids > sintético) e
profundidade histórica (nº de safras no `YieldRecord`). O tier (LOW/MEDIUM/
HIGHER) sobe com mais safras, mas é rebaixado se os dados subjacentes forem
majoritariamente sintéticos — a classificação é sempre calculada, nunca
arbitrária, como a spec exige.

## 5. Economic Engine + Monte Carlo (spec seção 26-27)

`services/economic_engine.py` implementa margem de contribuição, margem
incremental, ROI, break-even de preço e produtividade. `services/
monte_carlo.py` aproxima a distribuição P10/P50/P90 da previsão por uma
normal (spread assimétrico calculado dos dois lados) e simula 1000 cenários
(configurável) variando produtividade, preço e resposta da intervenção,
retornando P5/P50/P95 de margem e probabilidade de lucro / ROI positivo.

## 6. Decision Engine (spec seção 24, 28-29)

`services/decision_engine.py` é o diferencial do produto: identifica sinais
de risco por regra (pH baixo, queda de NDVI, déficit hídrico, alta
variabilidade espacial), precifica cada intervenção candidata via Economic
Engine + Monte Carlo, e classifica `ACTION` / `MONITOR` / `DO_NOT_ACT` por
ROI esperado, probabilidade de ROI positivo e confiança — nunca só pelo
ganho de produtividade. Toda recomendação carrega o aviso de "Decision
Support, validar com responsável agronômico" (Agronomic Safety Layer, seção
29).

## 7. O que fica fora desta implementação (Fase 2/3 — seções 60-63)

- Grid de `SpatialCell` populado automaticamente por resolução configurável.
- Ingestão raster real de CHIRPS/ERA5-Land/MapBiomas.
- IoT (seção 7), sensores LoRaWAN/MQTT.
- LightGBMClassifier de risco treinado em outcomes reais.
- Modelos personalizados por fazenda / regionais (além da calibração simples
  já implementada).
- Copilot conversacional (seção 69) — o LLM explicaria previsões já
  produzidas pelo Decision Engine, nunca calcularia a previsão em si.
- Causal/uplift modeling para efeito de tratamento individual (seção 65).
- MLflow real (hoje: registry em memória por processo, `ml/model_registry.py`).
- Multi-tenancy é aplicada em todas as tabelas de domínio, mas RBAC (spec
  seção 49) hoje só distingue `role` no token — não há matriz de permissões
  por endpoint além do isolamento de tenant.

## 8. Geometria e banco de dados

O MVP roda em SQLite com geometrias armazenadas como GeoJSON em colunas
`JSON` (`app/models.py`), não como `geometry` nativo do PostGIS — isso
elimina a dependência de GDAL/PostGIS para rodar localmente com zero
configuração. `DATABASE_URL` aponta para PostgreSQL+PostGIS em produção
(`app/database.py` já cria a extensão PostGIS on-startup quando detecta um
DSN Postgres); a migração das colunas de geometria para `Geometry` via
GeoAlchemy2 fica registrada aqui como próximo passo antes de precisar de
consultas espaciais server-side (`ST_Intersects`, grid de células, etc.).
