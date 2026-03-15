/**
 * Monte Carlo simulation engine for portfolio return prediction.
 *
 * Model: Geometric Brownian Motion with monthly steps.
 *   r_t = (μ - σ²/2)/12  +  (σ/√12) · ε    where ε ~ N(0,1)
 *
 * Portfolio with monthly contributions is simulated N times.
 * Output: percentile fan data, VaR, probability of loss, Sharpe.
 */

// ─── Box-Muller: efficient standard-normal random draw ────────────────────────
function randn() {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// ─── Asset-class annual parameters ────────────────────────────────────────────
// mu = expected annual return (real, in BRL)
// sigma = annual standard deviation (volatility)
// Sources: B3/ANBIMA historical statistics, academic studies on Brazilian market
function buildAssetParams(selic, ipcaAnual) {
  const rf = selic / 100;        // risk-free (SELIC)
  const inf = ipcaAnual / 100;   // inflation

  return {
    // IBOV historical: ~8% real premium over risk-free; σ ~26%
    acoesBR: { mu: rf + 0.075, sigma: 0.26 },
    // S&P500 in BRL: USD return + currency carry; σ slightly lower due to diversification
    acoesExt: { mu: 0.03 + 0.085, sigma: 0.21 },
    // Renda Fixa: 95% CDI (CDB/LCI/LCA/TD) — low σ reflects mark-to-market on IPCA+
    rendaFixa: { mu: rf * 0.95, sigma: 0.025 },
    // FIIs: inflation + 5% real premium; σ ~14% (less than equities)
    fundos: { mu: inf + 0.05, sigma: 0.14 },
    // Reserva: 100% SELIC — essentially risk-free in nominal terms
    reserva: { mu: rf, sigma: 0.005 },
  };
}

/**
 * Run Monte Carlo simulation.
 *
 * @param {Object} allocation   - { acoesBR, acoesExt, rendaFixa, fundos, reserva } in %
 * @param {number} selic        - annual SELIC rate (%)
 * @param {number} ipcaAnual    - annual IPCA (%)
 * @param {number} monthlyAmount - monthly contribution in BRL
 * @param {number} years         - investment horizon
 * @param {number} simulations   - number of Monte Carlo paths (default 2000)
 * @returns {Object} simulation results
 */
export function runMonteCarlo({
  allocation,
  selic,
  ipcaAnual,
  monthlyAmount,
  years,
  simulations = 2000,
}) {
  const params = buildAssetParams(selic, ipcaAnual);
  const months = years * 12;

  // Portfolio-level weighted mu and sigma (simplified: ignore cross-correlations for now)
  const keys = ["acoesBR", "acoesExt", "rendaFixa", "fundos", "reserva"];
  const w = keys.map((k) => (allocation[k] || 0) / 100);

  const portMu = keys.reduce((s, k, i) => s + w[i] * params[k].mu, 0);
  // Approximate portfolio σ via weighted quadratic sum (assumes low cross-correlation)
  const portSigma = Math.sqrt(
    keys.reduce((s, k, i) => s + Math.pow(w[i] * params[k].sigma, 2), 0)
  );

  const muM = portMu / 12;
  const sigM = portSigma / Math.sqrt(12);
  const totalInvested = monthlyAmount * months;

  // ── Run simulations ─────────────────────────────────────────────────────────
  // Store annual snapshots per path: allPaths[sim][year]
  const finalValues = new Float64Array(simulations);
  // yearlyBuckets[y] = array of portfolio values at year y across all sims
  const yearlyBuckets = Array.from({ length: years + 1 }, () => new Float64Array(simulations));

  for (let sim = 0; sim < simulations; sim++) {
    let pf = 0;
    yearlyBuckets[0][sim] = 0;
    for (let m = 0; m < months; m++) {
      // GBM monthly return: drift-adjusted + noise
      const r = muM - 0.5 * sigM * sigM + sigM * randn();
      pf = (pf + monthlyAmount) * Math.exp(r);
      if ((m + 1) % 12 === 0) {
        yearlyBuckets[(m + 1) / 12][sim] = pf;
      }
    }
    finalValues[sim] = pf;
  }

  // ── Percentile helper ────────────────────────────────────────────────────────
  function percentile(sorted, p) {
    return sorted[Math.floor(sorted.length * p)] ?? sorted[sorted.length - 1];
  }

  // ── Yearly fan data ──────────────────────────────────────────────────────────
  const fanData = yearlyBuckets.map((bucket, year) => {
    const sorted = Array.from(bucket).sort((a, b) => a - b);
    const invested = monthlyAmount * year * 12;
    return {
      year,
      p5:  percentile(sorted, 0.05),
      p25: percentile(sorted, 0.25),
      p50: percentile(sorted, 0.50),
      p75: percentile(sorted, 0.75),
      p95: percentile(sorted, 0.95),
      invested,
    };
  });

  // ── Final-value statistics ───────────────────────────────────────────────────
  const sortedFinal = Array.from(finalValues).sort((a, b) => a - b);
  const probLoss = sortedFinal.filter((v) => v < totalInvested).length / simulations;
  const median = percentile(sortedFinal, 0.5);
  const var95  = percentile(sortedFinal, 0.05); // 5th pct = 95% VaR loss threshold
  const var99  = percentile(sortedFinal, 0.01);
  const best   = percentile(sortedFinal, 0.95);

  // Annualized return on median outcome
  const cagr = median > 0 ? (Math.pow(median / totalInvested, 1 / years) - 1) * 100 : 0;

  // Sharpe ratio (annualised, excess over SELIC)
  const sharpe = portSigma > 0 ? (portMu - selic / 100) / portSigma : 0;

  // Expected shortfall (CVaR at 95%): mean of worst 5%
  const worst5 = sortedFinal.slice(0, Math.floor(simulations * 0.05));
  const cvar95 = worst5.reduce((s, v) => s + v, 0) / (worst5.length || 1);

  return {
    fanData,
    probLoss: +(probLoss * 100).toFixed(1),
    median,
    var95,
    var99,
    cvar95,
    best,
    totalInvested,
    cagr: +cagr.toFixed(2),
    portMuPct: +(portMu * 100).toFixed(2),
    portSigmaPct: +(portSigma * 100).toFixed(2),
    sharpe: +sharpe.toFixed(2),
  };
}

// ─── Product recommendations ───────────────────────────────────────────────────

const RISK_LABELS = { 1: "Mínimo", 2: "Baixo", 3: "Médio", 4: "Moderado-Alto", 5: "Alto" };

/**
 * Returns specific Brazilian financial products per asset class,
 * with allocation amounts and contextual descriptions.
 */
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
        {
          ticker: "BOVA11",
          type: "ETF",
          risk: 4,
          desc: `Replica o Ibovespa (~80 empresas). Maior liquidez do segmento.`,
          splitPct: 50,
        },
        {
          ticker: "SMALL11",
          type: "ETF",
          risk: 5,
          desc: "Small caps brasileiras — maior potencial de crescimento.",
          splitPct: 30,
        },
        {
          ticker: "PIBB11",
          type: "ETF",
          risk: 4,
          desc: "Ibovespa ponderado por free float — taxa menor que BOVA11.",
          splitPct: 20,
        },
      ],
    },
    {
      catKey: "acoesExt",
      catLabel: "Ações Exterior",
      catColor: "#1B4965",
      catIcon: "🌐",
      products: [
        {
          ticker: "IVVB11",
          type: "ETF",
          risk: 4,
          desc: "S&P 500 em BRL (iShares/BlackRock). Principal referência global.",
          splitPct: 50,
        },
        {
          ticker: "ACWI11",
          type: "ETF",
          risk: 3,
          desc: "MSCI All Country World — +50 mercados, máxima diversificação.",
          splitPct: 30,
        },
        {
          ticker: "NASD11",
          type: "ETF",
          risk: 5,
          desc: "Nasdaq-100 (tech/growth). Alta volatilidade, alto potencial.",
          splitPct: 20,
        },
      ],
    },
    {
      catKey: "rendaFixa",
      catLabel: "Renda Fixa",
      catColor: "#D4A373",
      catIcon: "🏛️",
      products: [
        {
          ticker: "Tesouro Selic",
          type: "Título Público",
          risk: 1,
          desc: `Pós-fixado, ${sel}% a.a. D+1. Soberano — sem risco de crédito.`,
          splitPct: 30,
        },
        {
          ticker: "Tesouro IPCA+ 2035",
          type: "Título Público",
          risk: 2,
          desc: `IPCA (${ipca}% a.a.) + prêmio real. Protege contra inflação.`,
          splitPct: 30,
        },
        {
          ticker: "CDB 110% CDI",
          type: "Banco Digital",
          risk: 2,
          desc: "Garantido pelo FGC (até R$ 250 mil). Liquidez diária ou no vencimento.",
          splitPct: 20,
        },
        {
          ticker: "LCI/LCA isento IR",
          type: "Banco/Agro",
          risk: 2,
          desc: "Isenção de IR para PF equivale a ~115% CDI bruto.",
          splitPct: 20,
        },
      ],
    },
    {
      catKey: "fundos",
      catLabel: "Fundos e Alternativos",
      catColor: "#6B5B95",
      catIcon: "📦",
      products: [
        {
          ticker: "HGLG11",
          type: "FII — Logística",
          risk: 3,
          desc: "Galpões logísticos premium. DY histórico ~8-10% a.a.",
          splitPct: 30,
        },
        {
          ticker: "XPML11",
          type: "FII — Shopping",
          risk: 3,
          desc: "Portfólio de shoppings A+. Renda + valorização de cotas.",
          splitPct: 25,
        },
        {
          ticker: "IMAB11",
          type: "ETF — RF",
          risk: 2,
          desc: `Índice IMA-B (NTN-B). Alternativa a Tesouro IPCA+ com liquidez de ETF.`,
          splitPct: 25,
        },
        {
          ticker: "GOLD11",
          type: "ETF — Ouro",
          risk: 3,
          desc: "Ouro em BRL. Proteção contra cauda de risco e dólar alto.",
          splitPct: 20,
        },
      ],
    },
    {
      catKey: "reserva",
      catLabel: "Reserva e Liquidez",
      catColor: "#8D99AE",
      catIcon: "🛡️",
      products: [
        {
          ticker: "Tesouro Selic",
          type: "Título Público",
          risk: 1,
          desc: `${sel}% a.a. Resgate em D+1. Proteção máxima do capital.`,
          splitPct: 60,
        },
        {
          ticker: "CDB D+0 100% CDI",
          type: "Banco Digital",
          risk: 1,
          desc: "Liquidez imediata. Garantido pelo FGC. Nubank, Inter, C6, PicPay.",
          splitPct: 40,
        },
      ],
    },
  ];

  return catalog
    .filter(({ catKey }) => (allocation[catKey] || 0) >= 3)
    .map(({ catKey, catLabel, catColor, catIcon, products }) => {
      const catPct  = allocation[catKey];
      const catAmount = (catPct / 100) * amount;
      return {
        catKey,
        catLabel,
        catColor,
        catIcon,
        catPct,
        catAmount,
        products: products.map((p) => ({
          ...p,
          amount: (p.splitPct / 100) * catAmount,
          riskLabel: RISK_LABELS[p.risk],
        })),
      };
    });
}
