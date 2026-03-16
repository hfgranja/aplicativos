/**
 * Monte Carlo simulation engine — calibrated with each investor's philosophy.
 *
 * Model: Geometric Brownian Motion (monthly steps).
 *   r_t = (μ_eff - σ_eff²/2)/12  +  (σ_eff/√12) · ε    ε ~ N(0,1)
 *
 * Key concept: each investor profile modifies the BASE asset parameters
 * (derived from live BCB data) with their own μ-adjustment and σ-multiplier,
 * encoding their real-world investment edge/philosophy into the simulation.
 */

// ─── Box-Muller standard-normal draw ─────────────────────────────────────────
function randn() {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// ─── Base asset-class parameters (calibrated to BCB macro data) ──────────────
// mu  = expected annual total return (in BRL, nominal)
// sigma = annual standard deviation (volatility)
function buildBaseParams(selic, ipcaAnual) {
  const rf  = selic / 100;
  const inf = ipcaAnual / 100;
  return {
    acoesBR:  { mu: rf + 0.075, sigma: 0.26 },  // IBOV: RF + 7.5% equity premium
    acoesExt: { mu: 0.030 + 0.085, sigma: 0.21 }, // S&P500 in BRL: 11.5% nominal
    rendaFixa:{ mu: rf * 0.95,  sigma: 0.025 }, // ~95% CDI (CDB/LCI/LCA)
    fundos:   { mu: inf + 0.05, sigma: 0.14 },  // FIIs: IPCA + 5% real
    reserva:  { mu: rf,         sigma: 0.005 }, // Tesouro Selic: 100% SELIC
  };
}

// ─── Per-investor philosophy profiles ────────────────────────────────────────
// muAdj   : annual return adjustment added to base mu (e.g. +0.03 = +3 p.p.)
// sM      : sigma multiplier applied to base sigma (e.g. 0.75 = −25% vol)
//
// Rationale for each:
//  graham    : "Margem de segurança" — buys at discount → limited downside (↓σ),
//              conservative upside (↓μ on equities). High-quality bonds (↑μ RF).
//  buffett   : Quality-moat compounders → above-market returns (↑μ) with lower vol
//              than index thanks to durable competitive advantages (↓σ).
//  lynch     : GARP — growth stocks at fair price → higher μ and slightly higher σ.
//              "Invest in what you know" implies concentration risk.
//  templeton : Contrarian global — emerging markets at maximum pessimism → highest
//              expected μ on foreign equities but also highest σ (emerging-mkt vol).
//  soros     : Macro reflexivity + leverage → fat tails, largest σ of all profiles.
//              High expected μ when the thesis plays out, but severe drawdown risk.
//  dalio     : All Weather / risk parity — explicitly minimises σ across regimes;
//              small μ sacrifice for dramatically lower portfolio vol.
//  bogle     : Pure index — market return exactly, zero active premium or penalty.
//              Slight σ reduction from total-market diversification.
//  markowitz : Optimal frontier — diversification benefit lowers σ without reducing
//              expected μ (the "free lunch" of modern portfolio theory).
//  fama      : Small-cap/value factor tilt → +2 p.p. factor premium, slightly
//              higher σ from concentration in factor exposures.
//  sharpe    : CAPM market portfolio (β=1) → pure systematic risk/return, baseline.

export const INVESTOR_PROFILES = {
  graham: {
    acoesBR:  { muAdj: -0.020, sM: 0.75 },
    acoesExt: { muAdj: -0.020, sM: 0.75 },
    rendaFixa:{ muAdj: +0.010, sM: 0.80 },
    fundos:   { muAdj: +0.010, sM: 0.75 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.000,
    label: "Margem de segurança — ↓vol ×0.75, ↓μ ações",
  },
  buffett: {
    acoesBR:  { muAdj: +0.030, sM: 0.85 },
    acoesExt: { muAdj: +0.030, sM: 0.85 },
    rendaFixa:{ muAdj:  0.000, sM: 0.90 },
    fundos:   { muAdj: +0.020, sM: 0.85 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.000,
    label: "Moat quality — ↑μ +3%, ↓vol ×0.85",
  },
  lynch: {
    acoesBR:  { muAdj: +0.040, sM: 1.10 },
    acoesExt: { muAdj: +0.030, sM: 1.05 },
    rendaFixa:{ muAdj: -0.010, sM: 1.00 },
    fundos:   { muAdj: +0.020, sM: 1.05 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.000,
    label: "GARP — ↑μ +4%, ↑vol ×1.10",
  },
  templeton: {
    acoesBR:  { muAdj: +0.010, sM: 1.15 },
    acoesExt: { muAdj: +0.040, sM: 1.25 },
    rendaFixa:{ muAdj: +0.010, sM: 1.20 },
    fundos:   { muAdj: +0.020, sM: 1.20 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.000,
    label: "Contrarian global — ↑μExt +4%, ↑vol ×1.25",
  },
  soros: {
    acoesBR:  { muAdj: +0.030, sM: 1.40 },
    acoesExt: { muAdj: +0.050, sM: 1.50 },
    rendaFixa:{ muAdj: +0.020, sM: 1.30 },
    fundos:   { muAdj: +0.040, sM: 1.40 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.000,
    label: "Macro reflexivo — ↑μ +5%, ↑↑vol ×1.50",
  },
  dalio: {
    acoesBR:  { muAdj: -0.010, sM: 0.70 },
    acoesExt: { muAdj: -0.010, sM: 0.70 },
    rendaFixa:{ muAdj: +0.010, sM: 0.70 },
    fundos:   { muAdj: +0.010, sM: 0.65 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.005, // +0.5% rebalancing premium (All Weather quarterly)
    label: "All Weather — ↓↓vol ×0.70, rebalanceamento +0.5%",
  },
  bogle: {
    acoesBR:  { muAdj:  0.000, sM: 0.95 },
    acoesExt: { muAdj:  0.000, sM: 0.95 },
    rendaFixa:{ muAdj:  0.000, sM: 0.90 },
    fundos:   { muAdj:  0.000, sM: 0.90 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.0025, // +0.25% from disciplined annual rebalancing
    label: "Indexação passiva — mercado puro, ↓vol ×0.95",
  },
  markowitz: {
    acoesBR:  { muAdj:  0.000, sM: 0.80 },
    acoesExt: { muAdj:  0.000, sM: 0.80 },
    rendaFixa:{ muAdj:  0.000, sM: 0.80 },
    fundos:   { muAdj:  0.000, sM: 0.75 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.005, // explicit frontier optimisation harvests rebalancing bonus
    label: "Fronteira eficiente — ↓↓vol ×0.80, rebalanceamento +0.5%",
  },
  fama: {
    acoesBR:  { muAdj: +0.020, sM: 1.05 },
    acoesExt: { muAdj: +0.020, sM: 1.05 },
    rendaFixa:{ muAdj:  0.000, sM: 0.90 },
    fundos:   { muAdj: +0.010, sM: 1.00 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.0025,
    label: "Fatores small-value — ↑μ +2%, ↑vol ×1.05",
  },
  sharpe: {
    acoesBR:  { muAdj:  0.000, sM: 1.00 },
    acoesExt: { muAdj:  0.000, sM: 1.00 },
    rendaFixa:{ muAdj:  0.000, sM: 0.85 },
    fundos:   { muAdj:  0.000, sM: 0.95 },
    reserva:  { muAdj:  0.000, sM: 1.00 },
    rebalBonus: 0.0025,
    label: "CAPM β=1 — portfólio de mercado baseline",
  },
};

const ASSET_KEYS = ["acoesBR", "acoesExt", "rendaFixa", "fundos", "reserva"];

// ─── Blend philosopher profiles (equal weight) ───────────────────────────────
function blendProfiles(selectedIds) {
  const profiles = selectedIds
    .map((id) => INVESTOR_PROFILES[id])
    .filter(Boolean);

  if (profiles.length === 0) {
    // Neutral: no adjustment
    return {
      assetAdj: Object.fromEntries(ASSET_KEYS.map((k) => [k, { muAdj: 0, sM: 1 }])),
      rebalBonus: 0,
    };
  }

  const n = profiles.length;
  const assetAdj = {};
  ASSET_KEYS.forEach((key) => {
    assetAdj[key] = {
      muAdj: profiles.reduce((s, p) => s + p[key].muAdj, 0) / n,
      sM:    profiles.reduce((s, p) => s + p[key].sM, 0) / n,
    };
  });
  const rebalBonus = profiles.reduce((s, p) => s + p.rebalBonus, 0) / n;
  return { assetAdj, rebalBonus };
}

// ─── Main simulation ──────────────────────────────────────────────────────────
/**
 * Run Monte Carlo portfolio simulation.
 *
 * Three-layer calibration:
 *   Layer 1 — BCB macro base params (SELIC/IPCA driven)
 *   Layer 2 — Philosophy blend (investor profiles)
 *   Layer 3 — Live macro signals (EMBI+, Focus, IBOV, news sentiment)
 *
 * @param {Object}   allocation          - { acoesBR, acoesExt, rendaFixa, fundos, reserva } in %
 * @param {number}   selic               - annual SELIC rate (%)
 * @param {number}   ipcaAnual           - annual IPCA (%)
 * @param {number}   monthlyAmount       - monthly contribution (BRL)
 * @param {number}   years               - investment horizon
 * @param {string[]} selectedInvestorIds - philosopher IDs to blend into calibration
 * @param {Object}   macroAdjustment     - { muAdj, sigmaMultiplier } from fetchMacroSignals()
 * @param {number}   simulations         - Monte Carlo paths (default 2000)
 * @returns {Object} full simulation results
 */
export function runMonteCarlo({
  allocation,
  selic,
  ipcaAnual,
  monthlyAmount,
  years,
  selectedInvestorIds = [],
  macroAdjustment = null,
  simulations = 2000,
}) {
  // Layer 1: Base params from macro data
  const base = buildBaseParams(selic, ipcaAnual);

  // Layer 2: Blend investor philosophy profiles
  const { assetAdj, rebalBonus } = blendProfiles(selectedInvestorIds);

  // Layer 3: Live macro signal adjustments (applied uniformly to all asset classes)
  const macroMuAdj  = macroAdjustment?.muAdj          ?? 0;
  const macroSigmaM = macroAdjustment?.sigmaMultiplier ?? 1;

  // Apply layers 2 + 3 on top of base params
  const calibrated = {};
  ASSET_KEYS.forEach((key) => {
    const philoMu    = base[key].mu    + assetAdj[key].muAdj;
    const philoSigma = base[key].sigma * assetAdj[key].sM;
    calibrated[key] = {
      mu:        philoMu    + macroMuAdj,   // layer 3 mu shift
      sigma:     philoSigma * macroSigmaM,  // layer 3 sigma scale
      baseMu:    base[key].mu,
      baseSigma: base[key].sigma,
      philoMuAdj:  assetAdj[key].muAdj,
      philoSigmaM: assetAdj[key].sM,
      macroMuAdj,
      macroSigmaM,
    };
  });

  // Portfolio-level weighted mu and sigma
  const w = ASSET_KEYS.map((k) => (allocation[k] || 0) / 100);
  const portMuRaw = ASSET_KEYS.reduce((s, k, i) => s + w[i] * calibrated[k].mu, 0);
  const portMu    = portMuRaw + rebalBonus;  // add rebalancing premium
  const portSigma = Math.sqrt(
    ASSET_KEYS.reduce((s, k, i) => s + Math.pow(w[i] * calibrated[k].sigma, 2), 0)
  );

  const muM    = portMu / 12;
  const sigM   = portSigma / Math.sqrt(12);
  const months = years * 12;
  const totalInvested = monthlyAmount * months;

  // Run simulations
  const finalValues = new Float64Array(simulations);
  const yearlyBuckets = Array.from({ length: years + 1 }, () => new Float64Array(simulations));

  for (let sim = 0; sim < simulations; sim++) {
    let pf = 0;
    yearlyBuckets[0][sim] = 0;
    for (let m = 0; m < months; m++) {
      const r = muM - 0.5 * sigM * sigM + sigM * randn();
      pf = (pf + monthlyAmount) * Math.exp(r);
      if ((m + 1) % 12 === 0) {
        yearlyBuckets[(m + 1) / 12][sim] = pf;
      }
    }
    finalValues[sim] = pf;
  }

  // 6. Percentile helper
  const pct = (sorted, p) =>
    sorted[Math.min(Math.floor(sorted.length * p), sorted.length - 1)];

  // 7. Yearly fan data
  const fanData = yearlyBuckets.map((bucket, year) => {
    const sorted = Array.from(bucket).sort((a, b) => a - b);
    return {
      year,
      p5:  pct(sorted, 0.05),
      p25: pct(sorted, 0.25),
      p50: pct(sorted, 0.50),
      p75: pct(sorted, 0.75),
      p95: pct(sorted, 0.95),
      invested: monthlyAmount * year * 12,
    };
  });

  // 8. Final-value statistics
  const sortedFinal  = Array.from(finalValues).sort((a, b) => a - b);
  const probLoss     = sortedFinal.filter((v) => v < totalInvested).length / simulations;
  const median       = pct(sortedFinal, 0.50);
  const var95        = pct(sortedFinal, 0.05);
  const var99        = pct(sortedFinal, 0.01);
  const best         = pct(sortedFinal, 0.95);
  const worst5       = sortedFinal.slice(0, Math.floor(simulations * 0.05));
  const cvar95       = worst5.reduce((s, v) => s + v, 0) / (worst5.length || 1);
  const cagr         = median > 0 ? (Math.pow(median / totalInvested, 1 / years) - 1) * 100 : 0;
  const sharpe       = portSigma > 0 ? (portMu - selic / 100) / portSigma : 0;

  return {
    fanData,
    probLoss:        +(probLoss * 100).toFixed(1),
    median,
    var95,
    var99,
    cvar95,
    best,
    totalInvested,
    cagr:            +cagr.toFixed(2),
    portMuPct:       +(portMu * 100).toFixed(2),
    portSigmaPct:    +(portSigma * 100).toFixed(2),
    sharpe:          +sharpe.toFixed(2),
    calibratedParams: calibrated,   // for UI display
    rebalBonus:      +(rebalBonus * 100).toFixed(2),
  };
}

// ─── Philosophy blend analysis (for PhilosophyBlendCard UI) ──────────────────
/**
 * Returns a human-readable analysis of how each selected investor influences
 * the simulation model parameters.
 *
 * @param {string[]} selectedIds
 * @param {number}   selic
 * @param {number}   ipcaAnual
 * @returns {{ insights: Array, dominantStyle: string, blendedAdj: Object }}
 */
export function getPhilosophyBlend(selectedIds, selic, ipcaAnual) {
  const base   = buildBaseParams(selic, ipcaAnual);
  const { assetAdj, rebalBonus } = blendProfiles(selectedIds);

  // Per-investor contribution summary
  const insights = selectedIds
    .map((id) => {
      const p = INVESTOR_PROFILES[id];
      if (!p) return null;

      // Dominant effect: find asset with largest absolute influence
      const equityMuAdj = ((p.acoesBR.muAdj + p.acoesExt.muAdj) / 2 * 100).toFixed(1);
      const avgSigmaM   = ((p.acoesBR.sM + p.acoesExt.sM) / 2);
      const sigmaEffect = ((avgSigmaM - 1) * 100).toFixed(0);
      const sigmaLabel  = avgSigmaM < 1
        ? `↓vol ${(avgSigmaM * 100).toFixed(0)}%`
        : avgSigmaM > 1
        ? `↑vol ${(avgSigmaM * 100).toFixed(0)}%`
        : "vol mercado";
      const muLabel = +equityMuAdj > 0
        ? `↑μ +${equityMuAdj}%`
        : +equityMuAdj < 0
        ? `↓μ ${equityMuAdj}%`
        : "μ neutro";

      return {
        id,
        label: p.label,
        muLabel,
        sigmaLabel,
        sigmaEffect: +sigmaEffect,
        muAdjPct:    +equityMuAdj,
        rebalBonus:  +(p.rebalBonus * 100).toFixed(2),
      };
    })
    .filter(Boolean);

  // Dominant style: investor whose profile has the largest net effect
  let dominantStyle = "Mercado geral";
  if (selectedIds.length > 0) {
    const sorted = [...insights].sort(
      (a, b) => Math.abs(b.muAdjPct) + Math.abs(b.sigmaEffect) -
                (Math.abs(a.muAdjPct) + Math.abs(a.sigmaEffect))
    );
    if (sorted[0]) dominantStyle = sorted[0].label;
  }

  // Blended effective params (for the calibrated-params table)
  const blendedParams = {};
  ASSET_KEYS.forEach((key) => {
    blendedParams[key] = {
      mu:    +((base[key].mu    + assetAdj[key].muAdj) * 100).toFixed(2),
      sigma: +((base[key].sigma * assetAdj[key].sM)    * 100).toFixed(2),
      baseMu:    +(base[key].mu    * 100).toFixed(2),
      baseSigma: +(base[key].sigma * 100).toFixed(2),
      muDelta:   +(assetAdj[key].muAdj * 100).toFixed(2),
      sigmaM:    +assetAdj[key].sM.toFixed(3),
    };
  });

  return {
    insights,
    dominantStyle,
    blendedParams,
    rebalBonus: +(rebalBonus * 100).toFixed(2),
  };
}

// ─── Product recommendations (unchanged logic, kept here) ────────────────────

const RISK_LABELS = { 1: "Mínimo", 2: "Baixo", 3: "Médio", 4: "Moderado-Alto", 5: "Alto" };

export function getProductRecommendations({ allocation, amount, selic, ipcaAnual }) {
  const ipca = ipcaAnual.toFixed(1);
  const sel  = selic.toFixed(2);

  const catalog = [
    {
      catKey: "acoesBR",
      catLabel: "Ações Brasil",
      catColor: "#40916C",
      catIcon: "🇧🇷",
      products: [
        { ticker: "BOVA11",  type: "ETF",         risk: 4, desc: "Replica o Ibovespa (~80 empresas). Maior liquidez do segmento.",           splitPct: 50 },
        { ticker: "SMALL11", type: "ETF",         risk: 5, desc: "Small caps brasileiras — maior potencial de crescimento.",                   splitPct: 30 },
        { ticker: "PIBB11",  type: "ETF",         risk: 4, desc: "Ibovespa ponderado por free float — taxa menor que BOVA11.",                splitPct: 20 },
      ],
    },
    {
      catKey: "acoesExt",
      catLabel: "Ações Exterior",
      catColor: "#1B4965",
      catIcon: "🌐",
      products: [
        { ticker: "IVVB11",  type: "ETF",         risk: 4, desc: "S&P 500 em BRL (iShares/BlackRock). Principal referência global.",           splitPct: 50 },
        { ticker: "ACWI11",  type: "ETF",         risk: 3, desc: "MSCI All Country World — +50 mercados, máxima diversificação.",             splitPct: 30 },
        { ticker: "NASD11",  type: "ETF",         risk: 5, desc: "Nasdaq-100 (tech/growth). Alta volatilidade, alto potencial.",              splitPct: 20 },
      ],
    },
    {
      catKey: "rendaFixa",
      catLabel: "Renda Fixa",
      catColor: "#D4A373",
      catIcon: "🏛️",
      products: [
        { ticker: "Tesouro Selic",    type: "Título Público", risk: 1, desc: `Pós-fixado, ${sel}% a.a. D+1. Soberano — sem risco de crédito.`,         splitPct: 30 },
        { ticker: "Tesouro IPCA+ 2035", type: "Título Público", risk: 2, desc: `IPCA (${ipca}% a.a.) + prêmio real. Protege contra inflação.`,         splitPct: 30 },
        { ticker: "CDB 110% CDI",     type: "Banco Digital",  risk: 2, desc: "Garantido pelo FGC (até R$ 250 mil). Liquidez diária ou no vencimento.", splitPct: 20 },
        { ticker: "LCI/LCA isento IR",type: "Banco/Agro",     risk: 2, desc: "Isenção de IR para PF equivale a ~115% CDI bruto.",                     splitPct: 20 },
      ],
    },
    {
      catKey: "fundos",
      catLabel: "Fundos e Alternativos",
      catColor: "#6B5B95",
      catIcon: "📦",
      products: [
        { ticker: "HGLG11", type: "FII — Logística", risk: 3, desc: "Galpões logísticos premium. DY histórico ~8-10% a.a.",                  splitPct: 30 },
        { ticker: "XPML11", type: "FII — Shopping",  risk: 3, desc: "Portfólio de shoppings A+. Renda + valorização de cotas.",              splitPct: 25 },
        { ticker: "IMAB11", type: "ETF — RF",         risk: 2, desc: `Índice IMA-B (NTN-B). Alternativa a Tesouro IPCA+ com liquidez ETF.`,  splitPct: 25 },
        { ticker: "GOLD11", type: "ETF — Ouro",       risk: 3, desc: "Ouro em BRL. Proteção contra cauda de risco e dólar alto.",            splitPct: 20 },
      ],
    },
    {
      catKey: "reserva",
      catLabel: "Reserva e Liquidez",
      catColor: "#8D99AE",
      catIcon: "🛡️",
      products: [
        { ticker: "Tesouro Selic",    type: "Título Público", risk: 1, desc: `${sel}% a.a. Resgate em D+1. Proteção máxima do capital.`,    splitPct: 60 },
        { ticker: "CDB D+0 100% CDI", type: "Banco Digital",  risk: 1, desc: "Liquidez imediata. Garantido pelo FGC. Nubank, Inter, C6.",   splitPct: 40 },
      ],
    },
  ];

  return catalog
    .filter(({ catKey }) => (allocation[catKey] || 0) >= 3)
    .map(({ catKey, catLabel, catColor, catIcon, products }) => {
      const catPct    = allocation[catKey];
      const catAmount = (catPct / 100) * amount;
      return {
        catKey, catLabel, catColor, catIcon, catPct, catAmount,
        products: products.map((p) => ({
          ...p,
          amount: (p.splitPct / 100) * catAmount,
          riskLabel: RISK_LABELS[p.risk],
        })),
      };
    });
}
