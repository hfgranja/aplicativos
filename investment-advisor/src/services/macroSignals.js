/**
 * macroSignals.js — Real-time macro & news data layer
 *
 * Fetches live economic indicators and news from:
 *  1. BCB (Banco Central) — EMBI+ country risk, PIB, unemployment
 *  2. BCB Focus Report (OData) — market consensus forecasts
 *  3. brapi.dev — IBOVESPA live quote
 *  4. rss2json.com — InfoMoney headlines → NLP sentiment score
 *
 * All signals are combined into:
 *  • `signals[]` — individual indicator cards with status and model impact
 *  • `compositeScore` — 0 (bearish) → 100 (bullish)
 *  • `macroAdj` — { muAdj, sigmaMultiplier } applied on top of philosophy blend
 *  • `newsItems[]` — processed headline list for display
 */

const BCB_SERIES  = "https://api.bcb.gov.br/dados/serie/bcdata.sgs";
const BCB_FOCUS   = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata";
const BRAPI       = "https://brapi.dev/api";
const RSS2JSON    = "https://api.rss2json.com/v1/api.json";
const INFOMONEY_RSS = "https://www.infomoney.com.br/feed/";

// ─── Network helpers ──────────────────────────────────────────────────────────

function withTimeout(promise, ms = 6000) {
  return Promise.race([
    promise,
    new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms)),
  ]);
}

async function safeFetch(url, timeout = 6000) {
  try {
    const res = await withTimeout(fetch(url), timeout);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return null;
  }
}

// ─── BCB time-series (last value) ────────────────────────────────────────────

async function fetchBCBSeries(code) {
  const data = await safeFetch(`${BCB_SERIES}.${code}/dados/ultimos/5?formato=json`);
  if (!Array.isArray(data) || data.length === 0) return null;
  // return last non-null value
  for (let i = data.length - 1; i >= 0; i--) {
    const v = parseFloat(String(data[i]?.valor ?? "").replace(",", "."));
    if (!isNaN(v)) return v;
  }
  return null;
}

// BCB series codes:
//   3545  — EMBI+ Brazil country risk (spread bps)
//   7326  — PIB real % var. same quarter yoy
//   24369 — PNAD Contínua unemployment %

async function fetchBCBExtra() {
  const [embi, pib, unemployment] = await Promise.allSettled([
    fetchBCBSeries(3545),
    fetchBCBSeries(7326),
    fetchBCBSeries(24369),
  ]);
  return {
    embi:         embi.status         === "fulfilled" ? embi.value         : null,
    pibGrowth:    pib.status          === "fulfilled" ? pib.value          : null,
    unemployment: unemployment.status === "fulfilled" ? unemployment.value : null,
  };
}

// ─── BCB Focus Report — market consensus forecasts ───────────────────────────

async function fetchFocusIndicator(indicator) {
  const year  = new Date().getFullYear() + 1;
  const f     = `Indicador eq '${indicator}' and baseCalculo eq 0 and Ano eq ${year}`;
  const url   = `${BCB_FOCUS}/ExpectativasMercadoAnuais` +
    `?$top=1&$filter=${encodeURIComponent(f)}&$orderby=Data%20desc` +
    `&$format=json&$select=Indicador,Data,Ano,Mediana`;
  const data  = await safeFetch(url);
  const v     = data?.value?.[0]?.Mediana;
  return v != null ? parseFloat(String(v).replace(",", ".")) : null;
}

async function fetchFocusReport(currentSelic) {
  const [selicFocus, ipcaFocus, pibFocus, usdFocus] = await Promise.allSettled([
    fetchFocusIndicator("Selic"),
    fetchFocusIndicator("IPCA"),
    fetchFocusIndicator("PIB"),
    fetchFocusIndicator("Câmbio"),
  ]);
  return {
    selicFocus: selicFocus.status === "fulfilled" ? selicFocus.value : null,
    ipcaFocus:  ipcaFocus.status  === "fulfilled" ? ipcaFocus.value  : null,
    pibFocus:   pibFocus.status   === "fulfilled" ? pibFocus.value   : null,
    usdFocus:   usdFocus.status   === "fulfilled" ? usdFocus.value   : null,
  };
}

// ─── brapi.dev — IBOVESPA live quote ─────────────────────────────────────────

async function fetchIbovespa() {
  const data = await safeFetch(
    `${BRAPI}/quote/%5EBVSP?range=1mo&interval=1d&fundamental=false`,
    7000
  );
  const q = data?.results?.[0];
  if (!q) return null;
  return {
    price:      q.regularMarketPrice,
    change1d:   q.regularMarketChangePercent,
    prevClose:  q.regularMarketPreviousClose,
    yearHigh:   q.fiftyTwoWeekHigh,
    yearLow:    q.fiftyTwoWeekLow,
  };
}

// ─── News sentiment (InfoMoney via rss2json) ──────────────────────────────────

const POSITIVE_WORDS = [
  "alta", "subiu", "crescimento", "recuperação", "superávit", "lucro",
  "positivo", "aprovação", "expansão", "otimismo", "rally", "valorização",
  "recorde", "retomada", "estabilidade", "melhora", "reforma", "aceleração",
  "queda de juros", "queda da inflação", "resultados positivos", "ganhos",
];

const NEGATIVE_WORDS = [
  "queda", "caiu", "recessão", "déficit", "crise", "risco", "incerteza",
  "tensão", "perdas", "pessimismo", "desaceleração", "desemprego alto",
  "inadimplência", "pressão", "corte de empregos", "aumento de juros",
  "calote", "colapso", "instabilidade", "dívida", "estagflação",
  "contração", "retração", "prejuízo",
];

function scoreSentiment(text) {
  const lower = text.toLowerCase();
  let pos = 0, neg = 0;
  POSITIVE_WORDS.forEach((w) => { if (lower.includes(w)) pos++; });
  NEGATIVE_WORDS.forEach((w) => { if (lower.includes(w)) neg++; });
  if (pos + neg === 0) return 0.5;
  return pos / (pos + neg);
}

async function fetchNewsHeadlines() {
  const url  = `${RSS2JSON}?rss_url=${encodeURIComponent(INFOMONEY_RSS)}&count=20`;
  const data = await safeFetch(url, 9000);
  if (!data || data.status !== "ok" || !Array.isArray(data.items)) {
    return { items: [], sentiment: 0.5, available: false };
  }
  const items = data.items.slice(0, 15).map((item) => {
    const text      = (item.title || "") + " " + (item.description || "");
    const sentiment = scoreSentiment(text);
    return {
      title:     item.title || "",
      link:      item.link  || "",
      pubDate:   item.pubDate || "",
      sentiment,
      badge:     sentiment > 0.62 ? "positivo" : sentiment < 0.38 ? "negativo" : "neutro",
    };
  });
  const avg = items.length > 0
    ? items.reduce((s, i) => s + i.sentiment, 0) / items.length
    : 0.5;
  return { items, sentiment: +avg.toFixed(3), available: true };
}

// ─── Signal thresholds → model adjustments ───────────────────────────────────

const BRAZIL_SELIC_TARGET  = 3.0; // BCB long-run neutral rate (approx)
const BRAZIL_INFLATION_TARGET = 3.25; // official CMN target for 2026

function classifyEmbi(v) {
  if (v === null) return { status: "sem dados", color: "#555", muAdj: 0, sM: 1.00, score: 0 };
  if (v < 150)   return { status: "baixo",    color: "#40916C", muAdj: +0.005, sM: 0.97, score: +15 };
  if (v < 250)   return { status: "moderado", color: "#D4A373", muAdj:  0,     sM: 1.00, score:  0  };
  if (v < 350)   return { status: "elevado",  color: "#E67E22", muAdj: -0.010, sM: 1.08, score: -15 };
  if (v < 500)   return { status: "alto",     color: "#E94560", muAdj: -0.020, sM: 1.18, score: -25 };
  return           { status: "crítico",        color: "#8B0000", muAdj: -0.035, sM: 1.35, score: -40 };
}

function classifyPibFocus(v) {
  if (v === null) return { status: "sem dados", color: "#555", muAdj: 0, sM: 1.00, score: 0 };
  if (v > 3.0)   return { status: "forte",      color: "#40916C", muAdj: +0.010, sM: 0.97, score: +20 };
  if (v > 1.5)   return { status: "moderado",   color: "#D4A373", muAdj:  0,     sM: 1.00, score:  +5 };
  if (v > 0.5)   return { status: "fraco",      color: "#E67E22", muAdj: -0.005, sM: 1.00, score:  -5 };
  if (v > 0.0)   return { status: "estagnação", color: "#E94560", muAdj: -0.015, sM: 1.08, score: -20 };
  return           { status: "recessão",         color: "#8B0000", muAdj: -0.025, sM: 1.20, score: -35 };
}

function classifyIpcaFocus(v) {
  if (v === null) return { status: "sem dados", color: "#555", muAdj: 0, sM: 1.00, score: 0 };
  if (v <= BRAZIL_INFLATION_TARGET + 0.25)
    return { status: "na meta",     color: "#40916C", muAdj: +0.005, sM: 0.97, score: +10 };
  if (v <= 5.0)
    return { status: "acima meta",  color: "#D4A373", muAdj: -0.003, sM: 1.00, score:  -3 };
  if (v <= 7.0)
    return { status: "alto",        color: "#E67E22", muAdj: -0.010, sM: 1.05, score: -10 };
  return   { status: "muito alto",  color: "#E94560", muAdj: -0.020, sM: 1.15, score: -20 };
}

function classifySelicDirection(current, focus) {
  if (current === null || focus === null)
    return { status: "sem dados", color: "#555", muAdj: 0, sM: 1.00, score: 0 };
  const diff = focus - current;
  if (diff < -1.5)
    return { status: "afrouxamento forte", color: "#40916C", muAdj: +0.015, sM: 0.96, score: +15 };
  if (diff < -0.25)
    return { status: "afrouxando",         color: "#40916C", muAdj: +0.008, sM: 0.98, score:  +8 };
  if (diff < 0.25)
    return { status: "estável",            color: "#D4A373", muAdj:  0,     sM: 1.00, score:   0 };
  if (diff < 1.5)
    return { status: "aperto moderado",    color: "#E67E22", muAdj: -0.005, sM: 1.03, score:  -8 };
  return   { status: "aperto forte",      color: "#E94560", muAdj: -0.012, sM: 1.08, score: -15 };
}

function classifyIbovespa(ibov) {
  if (!ibov) return { status: "sem dados", color: "#555", muAdj: 0, sM: 1.00, score: 0 };
  const c1d = ibov.change1d ?? 0;
  if (c1d > 2.0)
    return { status: `+${c1d.toFixed(1)}% hoje`, color: "#40916C", muAdj: +0.004, sM: 0.98, score:  +5 };
  if (c1d > 0.5)
    return { status: `+${c1d.toFixed(1)}% hoje`, color: "#40916C", muAdj: +0.002, sM: 1.00, score:  +2 };
  if (c1d >= -0.5)
    return { status: `${c1d.toFixed(1)}% hoje`,  color: "#D4A373", muAdj:  0,     sM: 1.00, score:   0 };
  if (c1d >= -2.0)
    return { status: `${c1d.toFixed(1)}% hoje`,  color: "#E67E22", muAdj: -0.002, sM: 1.02, score:  -2 };
  return   { status: `${c1d.toFixed(1)}% hoje`,  color: "#E94560", muAdj: -0.005, sM: 1.06, score:  -5 };
}

function classifyUnemployment(v) {
  if (v === null) return { status: "sem dados", color: "#555", muAdj: 0, sM: 1.00, score: 0 };
  if (v < 7.0)   return { status: "pleno emprego", color: "#40916C", muAdj: +0.005, sM: 0.98, score: +10 };
  if (v < 9.5)   return { status: "moderado",      color: "#D4A373", muAdj:  0,     sM: 1.00, score:   0 };
  if (v < 12.0)  return { status: "elevado",        color: "#E67E22", muAdj: -0.005, sM: 1.03, score:  -8 };
  return           { status: "alto",                color: "#E94560", muAdj: -0.012, sM: 1.07, score: -15 };
}

function classifyNewsSentiment(score) {
  if (score >= 0.65) return { status: "positivo", color: "#40916C", muAdj: +0.004, sM: 0.98, score: +5 };
  if (score >= 0.48) return { status: "neutro",   color: "#D4A373", muAdj:  0,     sM: 1.00, score:  0 };
  if (score >= 0.35) return { status: "cauteloso",color: "#E67E22", muAdj: -0.003, sM: 1.02, score: -3 };
  return               { status: "negativo",      color: "#E94560", muAdj: -0.006, sM: 1.05, score: -6 };
}

// ─── Composite signal assembly ────────────────────────────────────────────────

function assembleSignals(raw, currentSelic) {
  const embiCls  = classifyEmbi(raw.embi);
  const pibCls   = classifyPibFocus(raw.pibFocus);
  const ipcaCls  = classifyIpcaFocus(raw.ipcaFocus);
  const selicCls = classifySelicDirection(currentSelic, raw.selicFocus);
  const ibovCls  = classifyIbovespa(raw.ibov);
  const unempCls = classifyUnemployment(raw.unemployment);
  const newsCls  = classifyNewsSentiment(raw.newsSentiment);

  const signals = [
    {
      id: "embi",
      name: "Risco Brasil (EMBI+)",
      icon: "🌎",
      value: raw.embi != null ? `${raw.embi.toFixed(0)} bps` : "—",
      valueRaw: raw.embi,
      description: "Prêmio de risco soberano brasileiro frente a T-Bills dos EUA",
      ...embiCls,
      impactDesc: embiCls.muAdj !== 0 || embiCls.sM !== 1
        ? `μ ${embiCls.muAdj >= 0 ? "+" : ""}${(embiCls.muAdj * 100).toFixed(1)}% · σ ×${embiCls.sM.toFixed(2)}`
        : "sem impacto",
    },
    {
      id: "pib",
      name: "PIB Esperado (Focus)",
      icon: "📈",
      value: raw.pibFocus != null ? `${raw.pibFocus.toFixed(1)}% a.a.` : "—",
      valueRaw: raw.pibFocus,
      description: "Mediana das expectativas do mercado para o crescimento do PIB",
      ...pibCls,
      impactDesc: pibCls.muAdj !== 0 || pibCls.sM !== 1
        ? `μ ${pibCls.muAdj >= 0 ? "+" : ""}${(pibCls.muAdj * 100).toFixed(1)}% · σ ×${pibCls.sM.toFixed(2)}`
        : "sem impacto",
    },
    {
      id: "ipca",
      name: "IPCA Esperado (Focus)",
      icon: "🔥",
      value: raw.ipcaFocus != null ? `${raw.ipcaFocus.toFixed(1)}% a.a.` : "—",
      valueRaw: raw.ipcaFocus,
      description: `Meta de inflação: ${BRAZIL_INFLATION_TARGET}%. Desvios elevam incerteza.`,
      ...ipcaCls,
      impactDesc: ipcaCls.muAdj !== 0 || ipcaCls.sM !== 1
        ? `μ ${ipcaCls.muAdj >= 0 ? "+" : ""}${(ipcaCls.muAdj * 100).toFixed(1)}% · σ ×${ipcaCls.sM.toFixed(2)}`
        : "sem impacto",
    },
    {
      id: "selic",
      name: "Direção da SELIC (Focus)",
      icon: "🏦",
      value: raw.selicFocus != null
        ? `${raw.selicFocus.toFixed(2)}% esperado vs ${currentSelic?.toFixed(2) ?? "—"}% atual`
        : "—",
      valueRaw: raw.selicFocus,
      description: "Tendência dos juros: afrouxamento favorece risco; aperto penaliza.",
      ...selicCls,
      impactDesc: selicCls.muAdj !== 0 || selicCls.sM !== 1
        ? `μ ${selicCls.muAdj >= 0 ? "+" : ""}${(selicCls.muAdj * 100).toFixed(1)}% · σ ×${selicCls.sM.toFixed(2)}`
        : "sem impacto",
    },
    {
      id: "ibovespa",
      name: "Ibovespa (Hoje)",
      icon: "📊",
      value: raw.ibov?.price != null
        ? `${raw.ibov.price.toLocaleString("pt-BR", { maximumFractionDigits: 0 })} pts`
        : "—",
      valueRaw: raw.ibov?.change1d,
      description: "Sinal de momentum do mercado acionário brasileiro.",
      ...ibovCls,
      impactDesc: ibovCls.muAdj !== 0 || ibovCls.sM !== 1
        ? `μ ${ibovCls.muAdj >= 0 ? "+" : ""}${(ibovCls.muAdj * 100).toFixed(1)}% · σ ×${ibovCls.sM.toFixed(2)}`
        : "sem impacto",
    },
    {
      id: "unemployment",
      name: "Desemprego (PNAD)",
      icon: "👥",
      value: raw.unemployment != null ? `${raw.unemployment.toFixed(1)}%` : "—",
      valueRaw: raw.unemployment,
      description: "Taxa de desocupação IBGE. Pleno emprego estimula consumo e lucros.",
      ...unempCls,
      impactDesc: unempCls.muAdj !== 0 || unempCls.sM !== 1
        ? `μ ${unempCls.muAdj >= 0 ? "+" : ""}${(unempCls.muAdj * 100).toFixed(1)}% · σ ×${unempCls.sM.toFixed(2)}`
        : "sem impacto",
    },
    {
      id: "news",
      name: "Sentimento das Notícias",
      icon: "📰",
      value: raw.newsAvailable
        ? `${(raw.newsSentiment * 100).toFixed(0)}% positivo`
        : "indisponível",
      valueRaw: raw.newsSentiment,
      description: "Análise de sentimento das últimas manchetes financeiras (InfoMoney).",
      ...newsCls,
      impactDesc: newsCls.muAdj !== 0 || newsCls.sM !== 1
        ? `μ ${newsCls.muAdj >= 0 ? "+" : ""}${(newsCls.muAdj * 100).toFixed(1)}% · σ ×${newsCls.sM.toFixed(2)}`
        : "sem impacto",
    },
  ];

  // Composite score: base 50 + weighted signal contributions
  const rawScore = 50 +
    embiCls.score  * 0.22 +  // country risk — highest weight
    pibCls.score   * 0.20 +  // growth
    ipcaCls.score  * 0.16 +  // inflation
    selicCls.score * 0.16 +  // monetary policy direction
    ibovCls.score  * 0.10 +  // momentum
    unempCls.score * 0.10 +  // labour market
    newsCls.score  * 0.06;   // sentiment — lowest weight

  const compositeScore = Math.round(Math.max(0, Math.min(100, rawScore)));

  // Net model adjustments (sum all signal adjustments)
  const netMuAdj = signals.reduce((s, sg) => s + sg.muAdj, 0);
  const netSigmaM = signals.reduce((s, sg) => s * sg.sM, 1.0);

  return {
    signals,
    compositeScore,
    macroAdj: {
      muAdj:          +netMuAdj.toFixed(4),
      sigmaMultiplier: +netSigmaM.toFixed(4),
    },
    riskLevel:
      compositeScore >= 70 ? "favorável"
      : compositeScore >= 50 ? "neutro"
      : compositeScore >= 30 ? "cauteloso"
      : "adverso",
    riskColor:
      compositeScore >= 70 ? "#40916C"
      : compositeScore >= 50 ? "#D4A373"
      : compositeScore >= 30 ? "#E67E22"
      : "#E94560",
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Fetch all macro signals and compute model adjustments.
 *
 * @param {number} currentSelic  - current SELIC from marketData (%)
 * @returns {Promise<Object>}    - { signals, compositeScore, macroAdj, riskLevel, newsItems }
 */
export async function fetchMacroSignals(currentSelic = 13.75) {
  const [bcbExtra, focus, ibovResult, newsResult] = await Promise.allSettled([
    fetchBCBExtra(),
    fetchFocusReport(currentSelic),
    fetchIbovespa(),
    fetchNewsHeadlines(),
  ]);

  const extra = bcbExtra.status === "fulfilled" ? bcbExtra.value : {};
  const fcst  = focus.status    === "fulfilled" ? focus.value    : {};
  const ibov  = ibovResult.status === "fulfilled" ? ibovResult.value : null;
  const news  = newsResult.status === "fulfilled" ? newsResult.value : { items: [], sentiment: 0.5, available: false };

  const raw = {
    embi:         extra.embi         ?? null,
    pibGrowth:    extra.pibGrowth    ?? null,
    unemployment: extra.unemployment ?? null,
    selicFocus:   fcst.selicFocus    ?? null,
    ipcaFocus:    fcst.ipcaFocus     ?? null,
    pibFocus:     fcst.pibFocus      ?? null,
    usdFocus:     fcst.usdFocus      ?? null,
    ibov,
    newsSentiment: news.sentiment,
    newsAvailable: news.available,
  };

  const result = assembleSignals(raw, currentSelic);
  return {
    ...result,
    rawData:   raw,
    newsItems: news.items,
    fetchedAt: new Date().toISOString(),
  };
}
