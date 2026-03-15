import { useState, useRef } from "react";

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
  { key: "acoesBR", label: "Ações Brasil", color: "#40916C", icon: "🇧🇷" },
  { key: "acoesExt", label: "Ações Exterior", color: "#1B4965", icon: "🌐" },
  { key: "rendaFixa", label: "Renda Fixa", color: "#D4A373", icon: "🏛️" },
  { key: "fundos", label: "Fundos e Alternativos", color: "#6B5B95", icon: "📦" },
  { key: "reserva", label: "Reserva e Liquidez", color: "#8D99AE", icon: "🛡️" },
];

const formatBRL = (v) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

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
                ? level <= 2
                  ? "#40916C"
                  : level <= 3
                  ? "#D4A373"
                  : "#E94560"
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
          <title>
            {a.label}: {a.value.toFixed(1)}%
          </title>
        </path>
      ))}
      <circle cx={cx} cy={cy} r={r * 0.55} fill="#0D0D12" />
    </svg>
  );
}

function BarH({ pct, color, label, amount, detail }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
          marginBottom: 4,
        }}
      >
        <span>{label}</span>
        <span style={{ color }}>
          {pct.toFixed(1)}% — {formatBRL(amount)}
        </span>
      </div>
      <div
        style={{
          background: "rgba(255,255,255,0.06)",
          borderRadius: 4,
          height: 18,
          overflow: "hidden",
        }}
      >
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
        <div style={{ fontSize: 10, color: "#888", marginTop: 2, fontStyle: "italic" }}>
          {detail}
        </div>
      )}
    </div>
  );
}

export default function InvestmentAdvisor() {
  const [amount, setAmount] = useState(5000);
  const [selected, setSelected] = useState(["buffett", "bogle"]);
  const [showResult, setShowResult] = useState(false);
  const [animIn, setAnimIn] = useState(false);
  const resultRef = useRef(null);

  const toggleInvestor = (id) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setShowResult(false);
  };

  const computeAllocation = () => {
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
    CATEGORIES.forEach(({ key }) => {
      avg[key] = (avg[key] / total) * 100;
    });
    return { avg, details };
  };

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
      ? Math.round(
          chosenInvestors.reduce((s, i) => s + i.riskLevel, 0) / chosenInvestors.length
        )
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
          <h1
            style={{
              fontSize: 32,
              fontWeight: 300,
              margin: 0,
              lineHeight: 1.2,
              letterSpacing: -0.5,
            }}
          >
            Conselheiro de
            <br />
            <span style={{ fontWeight: 700, color: "#D4A373" }}>Investimentos</span>
          </h1>
          <p
            style={{
              color: "#777",
              fontSize: 14,
              marginTop: 8,
              maxWidth: 500,
              lineHeight: 1.6,
            }}
          >
            Selecione os pensadores que ressoam com sua filosofia e receba uma sugestão
            de alocação mensal personalizada.
          </p>
        </div>
      </div>

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
              onChange={(e) => {
                setAmount(Number(e.target.value));
                setShowResult(false);
              }}
              style={{
                flex: 1,
                minWidth: 150,
                accentColor: "#D4A373",
                height: 4,
                cursor: "pointer",
              }}
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
            {
              title: "Investidores Práticos",
              ids: ["graham", "buffett", "lynch", "templeton", "soros", "dalio", "bogle"],
            },
            { title: "Teóricos Acadêmicos", ids: ["markowitz", "fama", "sharpe"] },
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
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          marginBottom: 8,
                        }}
                      >
                        <span style={{ fontSize: 20 }}>{inv.icon}</span>
                        <div>
                          <div style={{ fontSize: 15, fontWeight: 600, lineHeight: 1.2 }}>
                            {inv.name}
                          </div>
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
                      <div
                        style={{
                          fontSize: 12,
                          color: active ? "#bbb" : "#666",
                          lineHeight: 1.5,
                        }}
                      >
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
            background:
              selected.length > 0
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
          {selected.length === 0
            ? "Selecione ao menos um mentor"
            : "Gerar Alocação Mensal →"}
        </button>

        {/* Results */}
        {showResult && alloc && (
          <div
            ref={resultRef}
            style={{
              opacity: animIn ? 1 : 0,
              transform: animIn ? "translateY(0)" : "translateY(20px)",
              transition: "all 0.6s cubic-bezier(.22,1,.36,1)",
            }}
          >
            {/* Summary Header */}
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
                data={CATEGORIES.map((c) => ({
                  value: alloc.avg[c.key],
                  color: c.color,
                  label: c.label,
                }))}
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
                <div
                  style={{ fontSize: 36, fontWeight: 300, color: "#D4A373", marginBottom: 4 }}
                >
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
                    <div style={{ fontSize: 14 }}>
                      {chosenInvestors.map((i) => i.icon).join(" ")}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Allocation Bars */}
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
              Este é um exercício educacional baseado nas filosofias dos pensadores selecionados.
              Não constitui recomendação de investimento. Consulte um profissional certificado
              antes de tomar decisões financeiras. Rentabilidade passada não é garantia de
              retorno futuro.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
