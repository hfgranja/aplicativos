import { useState, useRef, useEffect, useCallback } from "react";
import { fetchMarketIndicators, INDICATOR_META } from "./services/financialData";
import { runMonteCarlo, getProductRecommendations, getPhilosophyBlend, INVESTOR_PROFILES } from "./services/monteCarlo";

// ─── Investor database ────────────────────────────────────────────────────────

const INVESTORS = [
  {
    id: "graham",
    name: "Benjamin Graham",
    tag: "Value Investing Clássico",
    icon: "📚",
    color: "#1B4332",
    accent: "#40916C",
    idea: "Comprar ativos bem abaixo do valor intrínseco, com grande margem de segurança.",
    allocation: {
      acoesBR: 25, acoesBRType: "Ações de valor (P/L baixo, P/VP < 1)",
      acoesExt: 10, acoesExtType: "Ações globais subvalorizadas",
      rendaFixa: 50, rendaFixaType: "Títulos públicos e CDBs de bancos sólidos",
      fundos: 10, fundosType: "FIIs com desconto sobre valor patrimonial",
      reserva: 5, reservaType: "Reserva de oportunidade em Tesouro Selic",
    },
    riskLevel: 2,
    horizon: "Longo prazo (5-10+ anos)",
    keyPrinciple: "Margem de segurança: nunca pague o preço cheio.",
  },
  {
    id: "buffett",
    name: "Warren Buffett",
    tag: "Value de Qualidade (Moat)",
    icon: "💎",
    color: "#3C1518",
    accent: "#A44A3F",
    idea: "Comprar negócios excelentes a preço justo e manter no longo prazo.",
    allocation: {
      acoesBR: 35, acoesBRType: "Blue chips com vantagem competitiva duradoura",
      acoesExt: 20, acoesExtType: "Empresas globais com moat (tech, consumo)",
      rendaFixa: 25, rendaFixaType: "Tesouro IPCA+ e debêntures de empresas sólidas",
      fundos: 15, fundosType: "FIIs de qualidade (shoppings, logística premium)",
      reserva: 5, reservaType: "Caixa para oportunidades excepcionais",
    },
    riskLevel: 3,
    horizon: "Longo prazo (10+ anos, idealmente para sempre)",
    keyPrinciple: "Compre empresas maravilhosas a um preço justo.",
  },
  {
    id: "lynch",
    name: "Peter Lynch",
    tag: "Growth at Reasonable Price",
    icon: "🔍",
    color: "#0D1B2A",
    accent: "#1B4965",
    idea: "Investir no que você conhece. Procurar empresas de crescimento a preço justo.",
    allocation: {
      acoesBR: 30, acoesBRType: "Small/mid caps em setores que você conhece bem",
      acoesExt: 20, acoesExtType: "Growth stocks globais com PEG < 1",
      rendaFixa: 20, rendaFixaType: "CDBs e LCIs de médio prazo",
      fundos: 20, fundosType: "Fundos de ações com foco em crescimento",
      reserva: 10, reservaType: "Liquidez para aproveitar descobertas",
    },
    riskLevel: 3,
    horizon: "Médio a longo prazo (3-10 anos)",
    keyPrinciple: "Invista no que você entende profundamente.",
  },
  {
    id: "templeton",
    name: "John Templeton",
    tag: "Contrarian Global",
    icon: "🌍",
    color: "#2D0320",
    accent: "#8B2252",
    idea: "Comprar o que todos odeiam, em múltiplos mercados, com foco no longo prazo.",
    allocation: {
      acoesBR: 15, acoesBRType: "Setores deprimidos no Brasil",
      acoesExt: 40, acoesExtType: "Mercados emergentes e ativos em crise global",
      rendaFixa: 20, rendaFixaType: "Bonds de países em recuperação",
      fundos: 15, fundosType: "ETFs de mercados emergentes e fronteira",
      reserva: 10, reservaType: "Reserva para crises = oportunidades",
    },
    riskLevel: 4,
    horizon: "Longo prazo (5-15 anos)",
    keyPrinciple: "O momento de máximo pessimismo é o melhor para comprar.",
  },
  {
    id: "soros",
    name: "George Soros",
    tag: "Macro e Reflexividade",
    icon: "⚡",
    color: "#1A1A2E",
    accent: "#E94560",
    idea: "Explorar ciclos alimentados por crenças auto-reforçadoras dos investidores.",
    allocation: {
      acoesBR: 15, acoesBRType: "Posições táticas baseadas em ciclos macro",
      acoesExt: 25, acoesExtType: "Apostas macro em moedas e índices globais",
      rendaFixa: 20, rendaFixaType: "Prefixados e IPCA+ conforme ciclo de juros",
      fundos: 30, fundosType: "Fundos multimercado macro e hedge funds",
      reserva: 10, reservaType: "Liquidez alta para movimentos rápidos",
    },
    riskLevel: 5,
    horizon: "Tático (meses a poucos anos)",
    keyPrinciple: "Identifique a narrativa dominante — e quando ela vai quebrar.",
  },
  {
    id: "dalio",
    name: "Ray Dalio",
    tag: "Macro Sistemático / All Weather",
    icon: "⚖️",
    color: "#1A1423",
    accent: "#6B5B95",
    idea: "Carteiras robustas a vários cenários econômicos com paridade de risco.",
    allocation: {
      acoesBR: 15, acoesBRType: "Ações diversificadas (índice amplo)",
      acoesExt: 15, acoesExtType: "Ações globais diversificadas",
      rendaFixa: 40, rendaFixaType: "Mix de Tesouro IPCA+, Prefixados e Selic",
      fundos: 20, fundosType: "Ouro, commodities e FIIs (proteção)",
      reserva: 10, reservaType: "Rebalanceamento trimestral",
    },
    riskLevel: 2,
    horizon: "Todos os horizontes (preparado para qualquer cenário)",
    keyPrinciple: "Diversifique entre regimes, não apenas entre ativos.",
  },
  {
    id: "bogle",
    name: "Jack Bogle",
    tag: "Indexação Passiva",
    icon: "📊",
    color: "#0B2027",
    accent: "#40798C",
    idea: "Replicar o mercado via índices baratos, focando em custos mínimos.",
    allocation: {
      acoesBR: 20, acoesBRType: "ETF BOVA11 ou PIBB11 (Ibovespa)",
      acoesExt: 30, acoesExtType: "ETF S&P 500 (IVVB11) e global (ACWI)",
      rendaFixa: 35, rendaFixaType: "Tesouro Direto (Selic + IPCA+)",
      fundos: 10, fundosType: "ETFs de renda fixa (ex: IMAB11)",
      reserva: 5, reservaType: "Emergência em Tesouro Selic",
    },
    riskLevel: 2,
    horizon: "Longo prazo (20+ anos, buy and hold)",
    keyPrinciple: "Não tente vencer o mercado. Seja o mercado.",
  },
  {
    id: "markowitz",
    name: "Harry Markowitz",
    tag: "Teoria Moderna do Portfólio",
    icon: "🎯",
    color: "#2B2D42",
    accent: "#8D99AE",
    idea: "Maximizar retorno para um dado nível de risco via diversificação na fronteira eficiente.",
    allocation: {
      acoesBR: 20, acoesBRType: "Cesta diversificada otimizada por correlação",
      acoesExt: 20, acoesExtType: "Ativos globais descorrelacionados",
      rendaFixa: 30, rendaFixaType: "Mix otimizado de pré e pós-fixados",
      fundos: 20, fundosType: "Alternativos: ouro, FIIs, commodities",
      reserva: 10, reservaType: "Rebalanceamento periódico",
    },
    riskLevel: 3,
    horizon: "Médio a longo prazo (ajustável ao perfil)",
    keyPrinciple: "Diversificação é o único 'almoço grátis' em finanças.",
  },
  {
    id: "fama",
    name: "Eugene Fama",
    tag: "Hipótese do Mercado Eficiente",
    icon: "📈",
    color: "#1B1B1E",
    accent: "#D4A373",
    idea: "Preços refletem toda informação disponível; é quase impossível bater o mercado consistentemente.",
    allocation: {
      acoesBR: 15, acoesBRType: "ETFs amplos de mercado brasileiro",
      acoesExt: 35, acoesExtType: "ETFs globais diversificados (baixo custo)",
      rendaFixa: 35, rendaFixaType: "Tesouro Direto diversificado",
      fundos: 10, fundosType: "ETFs de fatores (small value, momentum)",
      reserva: 5, reservaType: "Liquidez mínima necessária",
    },
    riskLevel: 2,
    horizon: "Longo prazo (passivo, sem market timing)",
    keyPrinciple: "Você não vai bater o mercado. Aceite e prospere com ele.",
  },
  {
    id: "sharpe",
    name: "William Sharpe",
    tag: "CAPM e Risco Sistemático",
    icon: "📐",
    color: "#212529",
    accent: "#ADB5BD",
    idea: "O retorno esperado é proporcional ao risco sistemático (beta). Avalie performance pelo índice de Sharpe.",
    allocation: {
      acoesBR: 20, acoesBRType: "Portfólio de mercado (beta = 1)",
      acoesExt: 25, acoesExtType: "Exposição ao portfólio global de mercado",
      rendaFixa: 35, rendaFixaType: "Ativo livre de risco (Tesouro Selic)",
      fundos: 15, fundosType: "Ajuste de beta conforme perfil de risco",
      reserva: 5, reservaType: "Taxa livre de risco como âncora",
    },
    riskLevel: 2,
    horizon: "Ajustável (beta define a agressividade)",
    keyPrinciple: "Só o risco sistemático é remunerado. Diversifique o resto.",
  },
];

const CATEGORIES = [
  { key: "acoesBR",  label: "Ações Brasil",         color: "#40916C", icon: "🇧🇷" },
  { key: "acoesExt", label: "Ações Exterior",        color: "#1B4965", icon: "🌐" },
  { key: "rendaFixa",label: "Renda Fixa",            color: "#D4A373", icon: "🏛️" },
  { key: "fundos",   label: "Fundos e Alternativos", color: "#6B5B95", icon: "📦" },
  { key: "reserva",  label: "Reserva e Liquidez",    color: "#8D99AE", icon: "🛡️" },
];

const HORIZONS = [
  { years: 1,  label: "1 ano" },
  { years: 3,  label: "3 anos" },
  { years: 5,  label: "5 anos" },
  { years: 10, label: "10 anos" },
  { years: 20, label: "20 anos" },
];

const formatBRL = (v) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

// ─── Small UI primitives ──────────────────────────────────────────────────────

function RiskBar({ level }) {
  return (
    <div style={{ display: "flex", gap: 3, alignItems: "center" }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          style={{
            width: 8,
            height: i <= level ? 14 + i * 3 : 10,
            borderRadius: 2,
            background:
              i <= level
                ? level <= 2 ? "#40916C" : level <= 3 ? "#D4A373" : "#E94560"
                : "rgba(255,255,255,0.1)",
            transition: "all 0.3s ease",
          }}
        />
      ))}
    </div>
  );
}

function DonutChart({ data, size = 180 }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  if (total === 0) return null;
  const cx = size / 2, cy = size / 2, r = size * 0.38;
  let cum = 0;
  const arcs = data
    .filter((d) => d.value > 0)
    .map((d) => {
      const start = cum;
      cum += (d.value / total) * 360;
      const end = cum;
      const s = ((start - 90) * Math.PI) / 180;
      const e = ((end - 90) * Math.PI) / 180;
      const large = end - start > 180 ? 1 : 0;
      const x1 = cx + r * Math.cos(s), y1 = cy + r * Math.sin(s);
      const x2 = cx + r * Math.cos(e), y2 = cy + r * Math.sin(e);
      return {
        ...d,
        path: `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`,
      };
    });
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {arcs.map((a, i) => (
        <path key={i} d={a.path} fill={a.color} opacity={0.85}>
          <title>{a.label}: {a.value.toFixed(1)}%</title>
        </path>
      ))}
      <circle cx={cx} cy={cy} r={r * 0.55} fill="#0D0D12" />
    </svg>
  );
}

function BarH({ pct, color, label, amount, detail }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
        <span>{label}</span>
        <span style={{ color }}>{pct.toFixed(1)}% — {formatBRL(amount)}</span>
      </div>
      <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 4, height: 18, overflow: "hidden" }}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: `linear-gradient(90deg, ${color}99, ${color})`,
            borderRadius: 4,
            transition: "width 0.6s cubic-bezier(.22,1,.36,1)",
          }}
        />
      </div>
      {detail && (
        <div style={{ fontSize: 10, color: "#888", marginTop: 2, fontStyle: "italic" }}>{detail}</div>
      )}
    </div>
  );
}

// ─── Market data bar ──────────────────────────────────────────────────────────

function MarketBar({ data, loading }) {
  const items = [
    { key: "selic",     label: "SELIC",    unit: "% a.a." },
    { key: "ipcaAnual", label: "IPCA",     unit: "% a.a." },
    { key: "cdi",       label: "CDI",      unit: "% a.a." },
    { key: "usd",       label: "USD/BRL",  unit: "R$" },
  ];

  return (
    <div
      style={{
        background: "rgba(212,163,115,0.06)",
        borderBottom: "1px solid rgba(212,163,115,0.12)",
        padding: "10px 24px",
        display: "flex",
        gap: 0,
        alignItems: "center",
        flexWrap: "wrap",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 9,
          letterSpacing: 2,
          color: "#555",
          textTransform: "uppercase",
          marginRight: 16,
          whiteSpace: "nowrap",
        }}
      >
        {loading ? "⟳ Consultando BCB…" : `BCB · ${data?.fetchedAt ?? ""}`}
      </div>
      {items.map(({ key, label, unit }) => (
        <div
          key={key}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "4px 16px",
            borderLeft: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          <span style={{ fontSize: 10, color: "#666", fontFamily: "'JetBrains Mono', monospace" }}>
            {label}
          </span>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 13,
              fontWeight: 600,
              color: loading ? "#444" : "#D4A373",
            }}
          >
            {loading
              ? "—"
              : key === "usd"
              ? `R$ ${data?.[key]?.toFixed(2) ?? "—"}`
              : `${data?.[key]?.toFixed(2) ?? "—"}%`}
          </span>
          {!loading && (
            <span style={{ fontSize: 9, color: "#555", fontFamily: "'JetBrains Mono', monospace" }}>
              {unit}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Fan chart (Monte Carlo distribution over time) ───────────────────────────

function FanChart({ fanData, years, totalInvested }) {
  if (!fanData || fanData.length < 2) return null;

  const W = 600, H = 260;
  const pad = { top: 16, right: 24, bottom: 36, left: 78 };
  const cW = W - pad.left - pad.right;
  const cH = H - pad.top - pad.bottom;

  const maxVal = Math.max(...fanData.map((d) => d.p95)) * 1.05;
  const xS = (yr) => (yr / years) * cW;
  const yS = (v)  => cH - (v / maxVal) * cH;

  const poly = (points) => points.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");

  const topPts    = fanData.map((d) => [xS(d.year), yS(d.p95)]);
  const botPts    = [...fanData].reverse().map((d) => [xS(d.year), yS(d.p5)]);
  const topMidPts = fanData.map((d) => [xS(d.year), yS(d.p75)]);
  const botMidPts = [...fanData].reverse().map((d) => [xS(d.year), yS(d.p25)]);
  const medPts    = fanData.map((d) => [xS(d.year), yS(d.p50)]);
  const invPts    = fanData.map((d) => [xS(d.year), yS(d.invested)]);

  // Y-axis ticks
  const tickCount = 5;
  const yTicks = Array.from({ length: tickCount + 1 }, (_, i) => (maxVal * i) / tickCount);

  // X-axis ticks
  const xTicks = fanData.map((d) => d.year);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      <g transform={`translate(${pad.left},${pad.top})`}>
        {/* Grid */}
        {yTicks.map((v, i) => (
          <line
            key={i}
            x1={0} y1={yS(v).toFixed(1)}
            x2={cW} y2={yS(v).toFixed(1)}
            stroke="rgba(255,255,255,0.05)" strokeWidth={1}
          />
        ))}

        {/* Outer band: p5–p95 */}
        <polygon
          points={poly([...topPts, ...botPts])}
          fill="#D4A373"
          opacity={0.08}
        />
        {/* Inner band: p25–p75 */}
        <polygon
          points={poly([...topMidPts, ...botMidPts])}
          fill="#D4A373"
          opacity={0.15}
        />

        {/* Total invested reference line */}
        <polyline
          points={poly(invPts)}
          fill="none"
          stroke="rgba(255,255,255,0.25)"
          strokeWidth={1.5}
          strokeDasharray="4 3"
        />

        {/* Median line */}
        <polyline
          points={poly(medPts)}
          fill="none"
          stroke="#D4A373"
          strokeWidth={2}
          strokeLinejoin="round"
        />

        {/* Y-axis labels */}
        {yTicks.map((v, i) => (
          <text
            key={i}
            x={-6} y={yS(v) + 4}
            textAnchor="end"
            fill="#555"
            fontSize={9}
            fontFamily="'JetBrains Mono', monospace"
          >
            {v >= 1e6
              ? `${(v / 1e6).toFixed(1)}M`
              : v >= 1e3
              ? `${(v / 1e3).toFixed(0)}k`
              : v.toFixed(0)}
          </text>
        ))}

        {/* X-axis labels */}
        {xTicks.map((yr) => (
          <text
            key={yr}
            x={xS(yr)} y={cH + 18}
            textAnchor="middle"
            fill="#555"
            fontSize={9}
            fontFamily="'JetBrains Mono', monospace"
          >
            {yr === 0 ? "Hoje" : `Ano ${yr}`}
          </text>
        ))}

        {/* Endpoint dot on median */}
        {medPts.length > 0 && (
          <circle
            cx={medPts[medPts.length - 1][0]}
            cy={medPts[medPts.length - 1][1]}
            r={4}
            fill="#D4A373"
          />
        )}
      </g>

      {/* Legend */}
      <g transform={`translate(${pad.left + 8}, ${H - 10})`}>
        <rect x={0} y={-6} width={10} height={6} fill="#D4A373" opacity={0.25} />
        <text x={14} y={0} fill="#555" fontSize={8} fontFamily="'JetBrains Mono', monospace">p5–p95</text>
        <rect x={56} y={-6} width={10} height={6} fill="#D4A373" opacity={0.4} />
        <text x={70} y={0} fill="#555" fontSize={8} fontFamily="'JetBrains Mono', monospace">p25–p75</text>
        <line x1={118} y1={-3} x2={128} y2={-3} stroke="#D4A373" strokeWidth={2} />
        <text x={132} y={0} fill="#555" fontSize={8} fontFamily="'JetBrains Mono', monospace">Mediana</text>
        <line x1={184} y1={-3} x2={194} y2={-3} stroke="rgba(255,255,255,0.3)" strokeWidth={1.5} strokeDasharray="3 2" />
        <text x={198} y={0} fill="#555" fontSize={8} fontFamily="'JetBrains Mono', monospace">Aportado</text>
      </g>
    </svg>
  );
}

// ─── Philosophy blend card ────────────────────────────────────────────────────

const ASSET_LABELS = {
  acoesBR:  "Ações BR",
  acoesExt: "Ações Ext.",
  rendaFixa:"Renda Fixa",
  fundos:   "Fundos",
  reserva:  "Reserva",
};

function PhilosophyBlendCard({ investorIds, marketData }) {
  if (!investorIds || investorIds.length === 0 || !marketData) return null;

  const blend = getPhilosophyBlend(
    investorIds,
    marketData.selic,
    marketData.ipcaAnual
  );

  const mono = { fontFamily: "'JetBrains Mono', monospace" };

  // Find investor metadata from INVESTORS list (icons)
  // We'll look it up from INVESTOR_PROFILES labels
  const profileLabels = INVESTOR_PROFILES;

  return (
    <div
      style={{
        background: "rgba(212,163,115,0.04)",
        border: "1px solid rgba(212,163,115,0.12)",
        borderRadius: 10,
        padding: "18px 20px",
        marginBottom: 18,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: 10,
          marginBottom: 14,
        }}
      >
        <div>
          <div style={{ ...mono, fontSize: 9, letterSpacing: 3, color: "#666", textTransform: "uppercase", marginBottom: 4 }}>
            Calibração da Filosofia
          </div>
          <div style={{ fontSize: 12, color: "#aaa", maxWidth: 420 }}>
            Parâmetros de retorno (μ) e risco (σ) ajustados pela blend dos mentores selecionados
          </div>
        </div>
        {blend.rebalBonus > 0 && (
          <div
            style={{
              background: "rgba(64,145,108,0.12)",
              border: "1px solid rgba(64,145,108,0.25)",
              borderRadius: 6,
              padding: "5px 10px",
              ...mono,
              fontSize: 10,
              color: "#40916C",
            }}
          >
            + {blend.rebalBonus}% bônus rebalanceamento/ano
          </div>
        )}
      </div>

      {/* Per-philosopher pills */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
        {blend.insights.map((ins) => (
          <div
            key={ins.id}
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 20,
              padding: "4px 10px",
              display: "flex",
              gap: 6,
              alignItems: "center",
            }}
          >
            <span style={{ ...mono, fontSize: 10, color: "#888" }}>
              {ins.id.charAt(0).toUpperCase() + ins.id.slice(1)}
            </span>
            <span
              style={{
                ...mono,
                fontSize: 9,
                color: ins.muAdjPct > 0 ? "#40916C" : ins.muAdjPct < 0 ? "#E94560" : "#666",
              }}
            >
              {ins.muLabel}
            </span>
            <span
              style={{
                ...mono,
                fontSize: 9,
                color: ins.sigmaEffect < 0 ? "#40916C" : ins.sigmaEffect > 0 ? "#E94560" : "#666",
              }}
            >
              {ins.sigmaLabel}
            </span>
          </div>
        ))}
      </div>

      {/* Calibrated params table */}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr>
              <th style={{ ...mono, fontSize: 9, color: "#555", textAlign: "left", padding: "4px 8px 8px 0", letterSpacing: 1, textTransform: "uppercase" }}>Classe</th>
              <th style={{ ...mono, fontSize: 9, color: "#555", textAlign: "right", padding: "4px 8px 8px", letterSpacing: 1, textTransform: "uppercase" }}>μ base</th>
              <th style={{ ...mono, fontSize: 9, color: "#40916C", textAlign: "right", padding: "4px 8px 8px", letterSpacing: 1, textTransform: "uppercase" }}>Δμ</th>
              <th style={{ ...mono, fontSize: 9, color: "#D4A373", textAlign: "right", padding: "4px 8px 8px", letterSpacing: 1, textTransform: "uppercase" }}>μ efetivo</th>
              <th style={{ ...mono, fontSize: 9, color: "#555", textAlign: "right", padding: "4px 8px 8px", letterSpacing: 1, textTransform: "uppercase" }}>σ base</th>
              <th style={{ ...mono, fontSize: 9, color: "#D4A373", textAlign: "right", padding: "4px 8px 8px", letterSpacing: 1, textTransform: "uppercase" }}>σ ×</th>
              <th style={{ ...mono, fontSize: 9, color: "#D4A373", textAlign: "right", padding: "4px 0 8px 8px", letterSpacing: 1, textTransform: "uppercase" }}>σ efetivo</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(blend.blendedParams).map(([key, p]) => {
              const muChanged    = Math.abs(p.muDelta) > 0.001;
              const sigmaChanged = Math.abs(p.sigmaM - 1) > 0.001;
              return (
                <tr key={key} style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
                  <td style={{ ...mono, fontSize: 10, color: "#888", padding: "6px 8px 6px 0" }}>
                    {ASSET_LABELS[key]}
                  </td>
                  <td style={{ ...mono, fontSize: 10, color: "#555", textAlign: "right", padding: "6px 8px" }}>
                    {p.baseMu}%
                  </td>
                  <td style={{ ...mono, fontSize: 10, textAlign: "right", padding: "6px 8px",
                    color: p.muDelta > 0.001 ? "#40916C" : p.muDelta < -0.001 ? "#E94560" : "#444" }}>
                    {p.muDelta > 0.001 ? `+${p.muDelta}%` : p.muDelta < -0.001 ? `${p.muDelta}%` : "—"}
                  </td>
                  <td style={{ ...mono, fontSize: 10, textAlign: "right", padding: "6px 8px",
                    color: muChanged ? "#D4A373" : "#666", fontWeight: muChanged ? 600 : 400 }}>
                    {p.mu}%
                  </td>
                  <td style={{ ...mono, fontSize: 10, color: "#555", textAlign: "right", padding: "6px 8px" }}>
                    {p.baseSigma}%
                  </td>
                  <td style={{ ...mono, fontSize: 10, textAlign: "right", padding: "6px 8px",
                    color: p.sigmaM < 0.999 ? "#40916C" : p.sigmaM > 1.001 ? "#E94560" : "#444" }}>
                    {sigmaChanged ? `×${p.sigmaM}` : "—"}
                  </td>
                  <td style={{ ...mono, fontSize: 10, textAlign: "right", padding: "6px 0 6px 8px",
                    color: sigmaChanged ? "#D4A373" : "#666", fontWeight: sigmaChanged ? 600 : 400 }}>
                    {p.sigma}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ ...mono, fontSize: 9, color: "#444", marginTop: 10, lineHeight: 1.6 }}>
        μ = retorno anual esperado (nominal, BRL) · σ = desvio padrão anual (volatilidade) ·
        Δμ e ×σ derivados da blend igualmente ponderada dos {investorIds.length} mentor{investorIds.length > 1 ? "es" : ""} selecionado{investorIds.length > 1 ? "s" : ""}
      </div>
    </div>
  );
}

// ─── Prediction panel ─────────────────────────────────────────────────────────

function MetricCard({ label, value, sub, color = "#D4A373", alert = false }) {
  return (
    <div
      style={{
        background: alert ? "rgba(233,69,96,0.08)" : "rgba(255,255,255,0.03)",
        border: `1px solid ${alert ? "rgba(233,69,96,0.2)" : "rgba(255,255,255,0.07)"}`,
        borderRadius: 10,
        padding: "14px 18px",
        flex: "1 1 140px",
        minWidth: 130,
      }}
    >
      <div
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 9,
          letterSpacing: 2,
          color: "#555",
          textTransform: "uppercase",
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 20, fontWeight: 600, color, lineHeight: 1.1 }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: "#666", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function PredictionPanel({ alloc, amount, marketData, horizon, onHorizonChange, investorIds = [] }) {
  const [simResult, setSimResult] = useState(null);
  const [running, setRunning] = useState(false);

  // Stable serialisation of investorIds for effect deps
  const investorKey = investorIds.slice().sort().join(",");

  useEffect(() => {
    if (!marketData) return;
    setRunning(true);

    // Defer to next tick so UI can show spinner first
    const t = setTimeout(() => {
      const result = runMonteCarlo({
        allocation: alloc,
        selic: marketData.selic,
        ipcaAnual: marketData.ipcaAnual,
        monthlyAmount: amount,
        years: horizon,
        selectedInvestorIds: investorIds,
        simulations: 2000,
      });
      setSimResult(result);
      setRunning(false);
    }, 30);

    return () => clearTimeout(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [alloc, amount, marketData, horizon, investorKey]);

  const mono = { fontFamily: "'JetBrains Mono', monospace" };

  return (
    <div
      style={{
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 12,
        padding: "24px",
        marginBottom: 20,
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <div style={{ ...mono, fontSize: 10, letterSpacing: 3, color: "#666", textTransform: "uppercase" }}>
          Análise Preditiva — Monte Carlo (2 000 simulações)
        </div>
        {/* Horizon selector */}
        <div style={{ display: "flex", gap: 6 }}>
          {HORIZONS.map(({ years, label }) => (
            <button
              key={years}
              onClick={() => onHorizonChange(years)}
              style={{
                ...mono,
                fontSize: 10,
                padding: "5px 10px",
                borderRadius: 6,
                border: horizon === years
                  ? "1px solid #D4A37388"
                  : "1px solid rgba(255,255,255,0.08)",
                background: horizon === years ? "rgba(212,163,115,0.12)" : "transparent",
                color: horizon === years ? "#D4A373" : "#555",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Philosophy calibration card */}
      <PhilosophyBlendCard investorIds={investorIds} marketData={marketData} />

      {/* Fan chart */}
      <div
        style={{
          background: "rgba(0,0,0,0.2)",
          borderRadius: 8,
          padding: "16px",
          marginBottom: 20,
          minHeight: 160,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {running || !simResult ? (
          <div style={{ ...mono, fontSize: 11, color: "#444" }}>
            Simulando cenários…
          </div>
        ) : (
          <FanChart
            fanData={simResult.fanData}
            years={horizon}
            totalInvested={simResult.totalInvested}
          />
        )}
      </div>

      {/* Metrics grid */}
      {simResult && !running && (
        <>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 10 }}>
            <MetricCard
              label="Patrimônio Mediano"
              value={formatBRL(simResult.median)}
              sub={`em ${horizon} ${horizon === 1 ? "ano" : "anos"} · CAGR ${simResult.cagr}%`}
            />
            <MetricCard
              label="Cenário Otimista (95%)"
              value={formatBRL(simResult.best)}
              sub="Melhor 5% das simulações"
              color="#40916C"
            />
            <MetricCard
              label="VaR 95% (pior caso)"
              value={formatBRL(simResult.var95)}
              sub={`CVaR: ${formatBRL(simResult.cvar95)}`}
              color="#E94560"
              alert
            />
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <MetricCard
              label="Total Aportado"
              value={formatBRL(simResult.totalInvested)}
              sub={`R$ ${amount.toLocaleString("pt-BR")}/mês × ${horizon * 12} meses`}
              color="#888"
            />
            <MetricCard
              label="Probabilidade de Perda"
              value={`${simResult.probLoss}%`}
              sub="Patrimônio < total aportado"
              color={simResult.probLoss < 15 ? "#40916C" : simResult.probLoss < 35 ? "#D4A373" : "#E94560"}
              alert={simResult.probLoss >= 35}
            />
            <MetricCard
              label="Índice de Sharpe"
              value={simResult.sharpe.toFixed(2)}
              sub={`Retorno esperado: ${simResult.portMuPct}% a.a. · Vol: ${simResult.portSigmaPct}%`}
              color={simResult.sharpe >= 1 ? "#40916C" : simResult.sharpe >= 0.5 ? "#D4A373" : "#E94560"}
            />
          </div>

          {/* Interpretation bar */}
          <div
            style={{
              marginTop: 14,
              padding: "12px 16px",
              background: "rgba(0,0,0,0.2)",
              borderRadius: 8,
              fontSize: 12,
              color: "#aaa",
              lineHeight: 1.6,
              fontStyle: "italic",
            }}
          >
            <span style={{ color: "#D4A373", fontStyle: "normal", fontWeight: 600 }}>Leitura: </span>
            Após {horizon} {horizon === 1 ? "ano" : "anos"} de aportes mensais de{" "}
            {formatBRL(amount)}, há {100 - simResult.probLoss}% de probabilidade de seu
            patrimônio superar o total investido ({formatBRL(simResult.totalInvested)}).
            Em 50% dos cenários você terá pelo menos {formatBRL(simResult.median)}.
            No pior 5% dos casos, o patrimônio fica em {formatBRL(simResult.var95)}.
            {simResult.rebalBonus > 0 && (
              <span style={{ color: "#40916C", fontStyle: "normal" }}>
                {" "}Inclui +{simResult.rebalBonus}% a.a. de bônus por rebalanceamento sistemático.
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Where to invest (product recommendations) ────────────────────────────────

function WhereToInvest({ alloc, amount, marketData }) {
  const recommendations = getProductRecommendations({
    allocation: alloc,
    amount,
    selic: marketData?.selic ?? 13.75,
    ipcaAnual: marketData?.ipcaAnual ?? 5.5,
  });

  const mono = { fontFamily: "'JetBrains Mono', monospace" };

  return (
    <div
      style={{
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 12,
        padding: "24px",
        marginBottom: 20,
      }}
    >
      <div style={{ ...mono, fontSize: 10, letterSpacing: 3, color: "#666", textTransform: "uppercase", marginBottom: 20 }}>
        Onde Aplicar — Produtos Recomendados
      </div>

      {recommendations.map(({ catKey, catLabel, catColor, catIcon, catPct, catAmount, products }) => (
        <div key={catKey} style={{ marginBottom: 24 }}>
          {/* Category header */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 10,
              paddingBottom: 8,
              borderBottom: `1px solid ${catColor}33`,
            }}
          >
            <span style={{ fontSize: 18 }}>{catIcon}</span>
            <div>
              <span style={{ fontSize: 14, fontWeight: 600, color: catColor }}>{catLabel}</span>
              <span style={{ ...mono, fontSize: 10, color: "#666", marginLeft: 10 }}>
                {catPct.toFixed(1)}% · {formatBRL(catAmount)}/mês
              </span>
            </div>
          </div>

          {/* Product cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))", gap: 8 }}>
            {products.map((p) => (
              <div
                key={p.ticker}
                style={{
                  background: "rgba(255,255,255,0.025)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  borderRadius: 8,
                  padding: "12px 14px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                  <div>
                    <span style={{ fontSize: 14, fontWeight: 700, color: "#E8E6E3" }}>{p.ticker}</span>
                    <span
                      style={{
                        ...mono,
                        fontSize: 8,
                        color: catColor,
                        background: `${catColor}22`,
                        padding: "2px 6px",
                        borderRadius: 3,
                        marginLeft: 6,
                      }}
                    >
                      {p.type}
                    </span>
                  </div>
                  <span
                    style={{
                      ...mono,
                      fontSize: 8,
                      color:
                        p.risk <= 2 ? "#40916C" : p.risk <= 3 ? "#D4A373" : "#E94560",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {p.riskLabel}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: "#777", lineHeight: 1.5, marginBottom: 8 }}>{p.desc}</div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ ...mono, fontSize: 9, color: "#555" }}>
                    {p.splitPct}% desta classe
                  </span>
                  <span style={{ ...mono, fontSize: 12, fontWeight: 600, color: catColor }}>
                    {formatBRL(p.amount)}/mês
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Summary table */}
      <div
        style={{
          marginTop: 8,
          padding: "14px 16px",
          background: "rgba(212,163,115,0.04)",
          border: "1px solid rgba(212,163,115,0.1)",
          borderRadius: 8,
        }}
      >
        <div style={{ ...mono, fontSize: 9, color: "#555", letterSpacing: 2, textTransform: "uppercase", marginBottom: 10 }}>
          Resumo da Carteira Mensal
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {recommendations.map(({ catKey, catLabel, catIcon, catColor, catAmount, catPct }) => (
            <div key={catKey} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span>{catIcon}</span>
              <span style={{ fontSize: 11, color: "#888" }}>{catLabel}</span>
              <span style={{ ...mono, fontSize: 11, color: catColor, fontWeight: 600 }}>
                {formatBRL(catAmount)}
              </span>
              <span style={{ ...mono, fontSize: 9, color: "#555" }}>({catPct.toFixed(0)}%)</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 10, borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 10, display: "flex", justifyContent: "space-between" }}>
          <span style={{ ...mono, fontSize: 10, color: "#666" }}>TOTAL MENSAL</span>
          <span style={{ ...mono, fontSize: 14, fontWeight: 700, color: "#D4A373" }}>
            {formatBRL(amount)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function InvestmentAdvisor() {
  const [amount, setAmount]       = useState(5000);
  const [selected, setSelected]   = useState(["buffett", "bogle"]);
  const [showResult, setShowResult] = useState(false);
  const [animIn, setAnimIn]       = useState(false);
  const [horizon, setHorizon]     = useState(10);
  const [marketData, setMarketData] = useState(null);
  const [marketLoading, setMarketLoading] = useState(true);
  const resultRef = useRef(null);

  // Fetch live BCB data once on mount
  useEffect(() => {
    setMarketLoading(true);
    fetchMarketIndicators().then((data) => {
      setMarketData(data);
      setMarketLoading(false);
    });
  }, []);

  const toggleInvestor = useCallback((id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setShowResult(false);
  }, []);

  const computeAllocation = useCallback(() => {
    if (selected.length === 0) return null;
    const chosen = INVESTORS.filter((i) => selected.includes(i.id));
    const avg = {};
    const details = {};
    CATEGORIES.forEach(({ key }) => {
      avg[key] = chosen.reduce((s, inv) => s + inv.allocation[key], 0) / chosen.length;
      const uniqueDetails = [...new Set(chosen.map((inv) => inv.allocation[key + "Type"]))];
      details[key] = uniqueDetails.join(" · ");
    });
    const total = Object.values(avg).reduce((s, v) => s + v, 0);
    CATEGORIES.forEach(({ key }) => { avg[key] = (avg[key] / total) * 100; });
    return { avg, details };
  }, [selected]);

  const handleGenerate = () => {
    setShowResult(true);
    setAnimIn(false);
    setTimeout(() => {
      setAnimIn(true);
      resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };

  const alloc = showResult ? computeAllocation() : null;
  const chosenInvestors = INVESTORS.filter((i) => selected.includes(i.id));
  const avgRisk =
    chosenInvestors.length > 0
      ? Math.round(chosenInvestors.reduce((s, i) => s + i.riskLevel, 0) / chosenInvestors.length)
      : 0;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0D0D12",
        color: "#E8E6E3",
        fontFamily: "'Crimson Pro', 'Georgia', serif",
        padding: 0,
        margin: 0,
      }}
    >
      <link
        href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
        rel="stylesheet"
      />

      {/* Header */}
      <div
        style={{
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          padding: "28px 24px 20px",
          background: "linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 100%)",
        }}
      >
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              letterSpacing: 4,
              color: "#666",
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            Portfolio Advisor
          </div>
          <h1 style={{ fontSize: 32, fontWeight: 300, margin: 0, lineHeight: 1.2, letterSpacing: -0.5 }}>
            Conselheiro de
            <br />
            <span style={{ fontWeight: 700, color: "#D4A373" }}>Investimentos</span>
          </h1>
          <p style={{ color: "#777", fontSize: 14, marginTop: 8, maxWidth: 500, lineHeight: 1.6 }}>
            Selecione os pensadores que ressoam com sua filosofia e receba uma sugestão
            de alocação mensal personalizada com modelo preditivo.
          </p>
        </div>
      </div>

      {/* Market data bar */}
      <MarketBar data={marketData} loading={marketLoading} />

      <div style={{ maxWidth: 800, margin: "0 auto", padding: "24px 24px 60px" }}>
        {/* Amount Input */}
        <div
          style={{
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 12,
            padding: "20px 24px",
            marginBottom: 28,
          }}
        >
          <label
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              letterSpacing: 3,
              color: "#666",
              textTransform: "uppercase",
              display: "block",
              marginBottom: 12,
            }}
          >
            Aporte Mensal
          </label>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontSize: 28, fontWeight: 300, color: "#D4A373" }}>R$</span>
            <input
              type="range"
              min={500}
              max={50000}
              step={500}
              value={amount}
              onChange={(e) => { setAmount(Number(e.target.value)); setShowResult(false); }}
              style={{ flex: 1, minWidth: 150, accentColor: "#D4A373", height: 4, cursor: "pointer" }}
            />
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 24,
                fontWeight: 500,
                color: "#E8E6E3",
                minWidth: 120,
                textAlign: "right",
              }}
            >
              {amount.toLocaleString("pt-BR")}
            </span>
          </div>
        </div>

        {/* Investor Selection */}
        <div style={{ marginBottom: 8 }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              letterSpacing: 3,
              color: "#666",
              textTransform: "uppercase",
              marginBottom: 14,
            }}
          >
            Selecione seus Mentores ({selected.length}/10)
          </div>

          {[
            { title: "Investidores Práticos", ids: ["graham", "buffett", "lynch", "templeton", "soros", "dalio", "bogle"] },
            { title: "Teóricos Acadêmicos",   ids: ["markowitz", "fama", "sharpe"] },
          ].map((group) => (
            <div key={group.title} style={{ marginBottom: 20 }}>
              <div
                style={{
                  fontSize: 11,
                  color: "#555",
                  fontFamily: "'JetBrains Mono', monospace",
                  letterSpacing: 1,
                  marginBottom: 10,
                  borderLeft: "2px solid #333",
                  paddingLeft: 10,
                }}
              >
                {group.title}
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
                  gap: 10,
                }}
              >
                {INVESTORS.filter((i) => group.ids.includes(i.id)).map((inv) => {
                  const active = selected.includes(inv.id);
                  return (
                    <button
                      key={inv.id}
                      onClick={() => toggleInvestor(inv.id)}
                      style={{
                        background: active
                          ? `linear-gradient(135deg, ${inv.color}, ${inv.color}dd)`
                          : "rgba(255,255,255,0.02)",
                        border: active
                          ? `1px solid ${inv.accent}88`
                          : "1px solid rgba(255,255,255,0.06)",
                        borderRadius: 10,
                        padding: "14px 16px",
                        cursor: "pointer",
                        textAlign: "left",
                        transition: "all 0.3s ease",
                        transform: active ? "scale(1.01)" : "scale(1)",
                        color: "#E8E6E3",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                        <span style={{ fontSize: 20 }}>{inv.icon}</span>
                        <div>
                          <div style={{ fontSize: 15, fontWeight: 600, lineHeight: 1.2 }}>{inv.name}</div>
                          <div
                            style={{
                              fontFamily: "'JetBrains Mono', monospace",
                              fontSize: 9,
                              color: active ? inv.accent : "#666",
                              letterSpacing: 1,
                              textTransform: "uppercase",
                            }}
                          >
                            {inv.tag}
                          </div>
                        </div>
                        <div style={{ marginLeft: "auto" }}>
                          <RiskBar level={inv.riskLevel} />
                        </div>
                      </div>
                      <div style={{ fontSize: 12, color: active ? "#bbb" : "#666", lineHeight: 1.5 }}>
                        {inv.idea}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={selected.length === 0}
          style={{
            width: "100%",
            padding: "16px",
            fontSize: 15,
            fontFamily: "'JetBrains Mono', monospace",
            fontWeight: 500,
            letterSpacing: 2,
            textTransform: "uppercase",
            background: selected.length > 0
              ? "linear-gradient(135deg, #D4A373, #A67C52)"
              : "rgba(255,255,255,0.05)",
            color: selected.length > 0 ? "#0D0D12" : "#555",
            border: "none",
            borderRadius: 10,
            cursor: selected.length > 0 ? "pointer" : "not-allowed",
            transition: "all 0.3s ease",
            marginBottom: 30,
          }}
        >
          {selected.length === 0 ? "Selecione ao menos um mentor" : "Gerar Alocação + Análise Preditiva →"}
        </button>

        {/* ── Results ── */}
        {showResult && alloc && (
          <div
            ref={resultRef}
            style={{
              opacity: animIn ? 1 : 0,
              transform: animIn ? "translateY(0)" : "translateY(20px)",
              transition: "all 0.6s cubic-bezier(.22,1,.36,1)",
            }}
          >
            {/* Summary donut */}
            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: 12,
                padding: "24px",
                marginBottom: 20,
                display: "flex",
                gap: 24,
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <DonutChart
                size={160}
                data={CATEGORIES.map((c) => ({ value: alloc.avg[c.key], color: c.color, label: c.label }))}
              />
              <div style={{ flex: 1, minWidth: 200 }}>
                <div
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 10,
                    letterSpacing: 3,
                    color: "#666",
                    textTransform: "uppercase",
                    marginBottom: 8,
                  }}
                >
                  Sua Alocação Sugerida
                </div>
                <div style={{ fontSize: 36, fontWeight: 300, color: "#D4A373", marginBottom: 4 }}>
                  {formatBRL(amount)}
                  <span style={{ fontSize: 14, color: "#888" }}>/mês</span>
                </div>
                <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 12 }}>
                  <div>
                    <div
                      style={{
                        fontSize: 10,
                        color: "#666",
                        fontFamily: "'JetBrains Mono', monospace",
                        marginBottom: 4,
                      }}
                    >
                      RISCO MÉDIO
                    </div>
                    <RiskBar level={avgRisk} />
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: 10,
                        color: "#666",
                        fontFamily: "'JetBrains Mono', monospace",
                        marginBottom: 4,
                      }}
                    >
                      MENTORES
                    </div>
                    <div style={{ fontSize: 14 }}>{chosenInvestors.map((i) => i.icon).join(" ")}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Allocation bars */}
            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: 12,
                padding: "24px",
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  letterSpacing: 3,
                  color: "#666",
                  textTransform: "uppercase",
                  marginBottom: 16,
                }}
              >
                Distribuição Detalhada
              </div>
              {CATEGORIES.map((c) => (
                <BarH
                  key={c.key}
                  pct={alloc.avg[c.key]}
                  color={c.color}
                  label={`${c.icon} ${c.label}`}
                  amount={(alloc.avg[c.key] / 100) * amount}
                  detail={alloc.details[c.key]}
                />
              ))}
            </div>

            {/* ── Monte Carlo Prediction Panel ── */}
            <PredictionPanel
              alloc={alloc.avg}
              amount={amount}
              marketData={marketData}
              horizon={horizon}
              onHorizonChange={setHorizon}
              investorIds={selected}
            />

            {/* ── Where to invest ── */}
            <WhereToInvest
              alloc={alloc.avg}
              amount={amount}
              marketData={marketData}
            />

            {/* Principles */}
            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: 12,
                padding: "24px",
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  letterSpacing: 3,
                  color: "#666",
                  textTransform: "uppercase",
                  marginBottom: 16,
                }}
              >
                Princípios dos seus Mentores
              </div>
              {chosenInvestors.map((inv) => (
                <div
                  key={inv.id}
                  style={{
                    display: "flex",
                    gap: 12,
                    alignItems: "flex-start",
                    marginBottom: 14,
                    padding: "12px",
                    background: `${inv.color}44`,
                    borderRadius: 8,
                    borderLeft: `3px solid ${inv.accent}`,
                  }}
                >
                  <span style={{ fontSize: 22 }}>{inv.icon}</span>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{inv.name}</div>
                    <div style={{ fontSize: 13, color: "#bbb", lineHeight: 1.5 }}>
                      &ldquo;{inv.keyPrinciple}&rdquo;
                    </div>
                    <div
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 9,
                        color: "#777",
                        marginTop: 4,
                      }}
                    >
                      Horizonte: {inv.horizon}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Disclaimer */}
            <div
              style={{
                fontSize: 11,
                color: "#555",
                lineHeight: 1.6,
                padding: "16px 20px",
                background: "rgba(255,255,255,0.02)",
                borderRadius: 8,
                border: "1px solid rgba(255,255,255,0.04)",
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              Modelo preditivo baseado em Geometric Brownian Motion com 2.000 simulações de
              Monte Carlo. Parâmetros calibrados com dados históricos do mercado brasileiro
              (B3/ANBIMA) e indicadores em tempo real do Banco Central do Brasil. Este
              material é exclusivamente educacional. Rentabilidade passada não garante
              resultados futuros. Consulte um assessor de investimentos certificado (CFP/CEA)
              antes de tomar decisões financeiras.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
