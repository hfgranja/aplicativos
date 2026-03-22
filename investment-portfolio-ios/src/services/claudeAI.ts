import * as SecureStore from 'expo-secure-store';
import { MarketQuote, TesouroBond, MarketIndices } from './marketData';
import { CategorySummary } from '../utils/categorizer';

const CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages';
const CLAUDE_MODEL = 'claude-sonnet-4-6';

export interface AISuggestion {
  id: string;
  type: 'portfolio' | 'spending' | 'market' | 'ir' | 'alert';
  title: string;
  content: string;
  actionable: string[];
  priority: 'high' | 'medium' | 'low';
  createdAt: Date;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface IRAnalysis {
  pgblOptimization: {
    estimatedAnnualIncome: number;
    maxDeduction: number;
    currentPGBL: number;
    potentialSaving: number;
    recommendation: string;
  };
  deductibleExpenses: {
    health: number;
    education: number;
    pension: number;
    total: number;
  };
  investmentIR: {
    type: string;
    rate: string;
    exemption: string;
  }[];
  alerts: string[];
  simulacao: string;
  strategy: string;
}

export async function getClaudeApiKey(): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync('claude_api_key');
  } catch {
    return null;
  }
}

async function callClaude(
  systemPrompt: string,
  userMessage: string,
  conversationHistory: ChatMessage[] = [],
  apiKey: string,
): Promise<string> {
  const messages = [
    ...conversationHistory.map(msg => ({
      role: msg.role,
      content: msg.content,
    })),
    { role: 'user', content: userMessage },
  ];

  const response = await fetch(CLAUDE_API_URL, {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: CLAUDE_MODEL,
      max_tokens: 2048,
      system: systemPrompt,
      messages,
    }),
    signal: AbortSignal.timeout(30000),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(`Claude API error ${response.status}: ${error?.error?.message || 'Unknown'}`);
  }

  const data = await response.json();
  return data?.content?.[0]?.text || '';
}

const FINANCIAL_ADVISOR_SYSTEM = `Você é o maior especialista do mundo em finanças pessoais e investimentos brasileiros.

Contexto do usuário:
- Meta: R$ 3.000.000 reais (valor real, já corrigido pela inflação)
- Aporte mensal: R$ 1.000/mês
- Aporte anual: R$ 200.000/ano
- Total anual: R$ 212.000
- Horizonte: 10-12 anos (plano base)
- Estratégia: 50-60% IPCA+, 20-30% pós-fixado, 15-25% crescimento

Regras de resposta:
- Sempre responda em português brasileiro
- Seja direto, executivo e acionável — sem rodeios
- Use números reais quando possível
- Quando sugerir investimentos, mencione onde comprar (plataformas)
- Considere sempre o contexto tributário brasileiro (IR, IOF, isenções)
- Foque no que move o ponteiro para o objetivo de R$ 3M`;

/**
 * Analyze current portfolio and provide investment suggestions
 */
export async function analyzePortfolio(
  portfolio: {
    value: number;
    allocation: { ipcaPlus: number; posFixed: number; growth: number };
    positions: Array<{ name: string; value: number; type: string }>;
  },
  marketData: { quotes: MarketQuote[]; indices: MarketIndices; bonds: TesouroBond[] },
): Promise<AISuggestion> {
  const apiKey = await getClaudeApiKey();
  if (!apiKey) {
    return {
      id: Date.now().toString(),
      type: 'portfolio',
      title: 'Configure sua API Key',
      content: 'Para análises com IA, configure sua chave da API Claude em Configurações.',
      actionable: ['Ir para Configurações → API Keys → Claude'],
      priority: 'high',
      createdAt: new Date(),
    };
  }

  const userMessage = `Analise meu portfólio atual:

**Patrimônio total:** R$ ${portfolio.value.toLocaleString('pt-BR')}

**Alocação atual:**
- IPCA+: ${portfolio.allocation.ipcaPlus}%
- Pós-fixado: ${portfolio.allocation.posFixed}%
- Crescimento: ${portfolio.allocation.growth}%

**Posições:**
${portfolio.positions.map(p => `- ${p.name}: R$ ${p.value.toLocaleString('pt-BR')} (${p.type})`).join('\n')}

**Mercado atual:**
- SELIC: ${marketData.indices.selic}% a.a.
- IPCA 12m: ${marketData.indices.ipca}%
- Ibovespa: ${marketData.indices.ibovespa.toLocaleString('pt-BR')} (${marketData.indices.ibovespaChange > 0 ? '+' : ''}${marketData.indices.ibovespaChange}%)
- USD/BRL: R$ ${marketData.indices.usdBrl}
- Tesouro IPCA+ 2035: IPCA + ${marketData.bonds.find(b => b.name.includes('2035'))?.annualRate || 5.5}%

Dê 3 sugestões acionáveis para otimizar meu portfólio em relação à meta de R$ 3M. Seja direto.`;

  try {
    const content = await callClaude(FINANCIAL_ADVISOR_SYSTEM, userMessage, [], apiKey);

    return {
      id: Date.now().toString(),
      type: 'portfolio',
      title: 'Análise do Portfólio',
      content,
      actionable: [],
      priority: 'medium',
      createdAt: new Date(),
    };
  } catch (error) {
    throw new Error(`Erro na análise: ${error instanceof Error ? error.message : 'Desconhecido'}`);
  }
}

/**
 * Analyze spending patterns and suggest savings
 */
export async function analyzeSpending(
  categories: CategorySummary[],
  monthlyContribution: number,
  goal: number = 3_000_000,
): Promise<AISuggestion> {
  const apiKey = await getClaudeApiKey();
  if (!apiKey) {
    return {
      id: Date.now().toString(),
      type: 'spending',
      title: 'Configure sua API Key',
      content: 'Para análise de gastos com IA, configure sua chave Claude em Configurações.',
      actionable: ['Configurações → API Keys → Claude'],
      priority: 'high',
      createdAt: new Date(),
    };
  }

  const totalSpending = categories.reduce((s, c) => s + c.total, 0);

  const userMessage = `Analise meus gastos do último mês:

**Total gasto:** R$ ${totalSpending.toLocaleString('pt-BR')}

**Por categoria:**
${categories.slice(0, 8).map(c => `- ${c.info.label}: R$ ${c.total.toLocaleString('pt-BR')} (${c.percentage.toFixed(1)}%)`).join('\n')}

**Contexto:** Meu aporte mensal atual é R$ ${monthlyContribution.toLocaleString('pt-BR')} e minha meta é R$ ${(goal / 1_000_000).toFixed(0)}M.

Como coach financeiro:
1. Identifique as 3 principais oportunidades de redução de gastos com valores específicos
2. Para cada redução sugerida, calcule o impacto na meta (quantos meses mais cedo atinjo R$ ${(goal / 1_000_000).toFixed(0)}M)
3. Dê dicas práticas e realistas para cada categoria

Seja direto e use números.`;

  try {
    const content = await callClaude(
      FINANCIAL_ADVISOR_SYSTEM + '\n\nFoque em análise de gastos pessoais e maximização de poupança.',
      userMessage,
      [],
      apiKey,
    );

    return {
      id: Date.now().toString(),
      type: 'spending',
      title: 'Oportunidades de Economia',
      content,
      actionable: [],
      priority: 'medium',
      createdAt: new Date(),
    };
  } catch (error) {
    throw new Error(`Erro na análise de gastos: ${error instanceof Error ? error.message : 'Desconhecido'}`);
  }
}

/**
 * Full IR (income tax) analysis
 */
export async function analyzeIR(
  investments: Array<{ name: string; type: string; value: number; purchaseDate?: string }>,
  deductibleExpenses: { health: number; education: number; pension: number },
  stockSalesThisMonth: number = 0,
): Promise<AISuggestion> {
  const apiKey = await getClaudeApiKey();
  if (!apiKey) {
    return {
      id: Date.now().toString(),
      type: 'ir',
      title: 'Configure sua API Key',
      content: 'Para análise de IR com IA, configure sua chave Claude em Configurações.',
      actionable: ['Configurações → API Keys → Claude'],
      priority: 'high',
      createdAt: new Date(),
    };
  }

  const userMessage = `Como o maior especialista em IR do Brasil, analise minha situação tributária:

**Meus investimentos:**
${investments.map(i => `- ${i.name} (${i.type}): R$ ${i.value.toLocaleString('pt-BR')}`).join('\n')}

**Gastos potencialmente dedutíveis (ano):**
- Saúde: R$ ${deductibleExpenses.health.toLocaleString('pt-BR')}
- Educação: R$ ${deductibleExpenses.education.toLocaleString('pt-BR')}
- Previdência (PGBL): R$ ${deductibleExpenses.pension.toLocaleString('pt-BR')}

**Vendas de ações este mês:** R$ ${stockSalesThisMonth.toLocaleString('pt-BR')}

Forneça:
1. **Otimização PGBL**: quanto contribuir para maximizar dedução (baseado em renda estimada)
2. **Resumo IR por investimento**: alíquota e quando incidir
3. **Despesas dedutíveis**: confirme o que posso deduzir e os limites
4. **Alertas**: isenção ações R$20k/mês, prazo declaração, DARF
5. **Estratégia tributária**: como estruturar para pagar menos IR legalmente
6. **Estimativa**: IR a pagar ou restituir esse ano

Use a legislação 2025/2026 mais atual. Seja preciso e acionável.`;

  try {
    const content = await callClaude(
      FINANCIAL_ADVISOR_SYSTEM + '\n\nEspecialidade: planejamento tributário brasileiro (IR, IRPF, DARF, PGBL, isenções).',
      userMessage,
      [],
      apiKey,
    );

    return {
      id: Date.now().toString(),
      type: 'ir',
      title: 'Análise Imposto de Renda',
      content,
      actionable: [],
      priority: 'high',
      createdAt: new Date(),
    };
  } catch (error) {
    throw new Error(`Erro na análise de IR: ${error instanceof Error ? error.message : 'Desconhecido'}`);
  }
}

/**
 * Chat with Claude — free-form financial questions
 */
export async function chat(
  message: string,
  history: ChatMessage[],
  context?: {
    portfolioValue?: number;
    marketIndices?: MarketIndices;
  },
): Promise<string> {
  const apiKey = await getClaudeApiKey();
  if (!apiKey) {
    return 'Para conversar com a IA, configure sua chave da API Claude em Configurações → API Keys → Claude.';
  }

  let systemWithContext = FINANCIAL_ADVISOR_SYSTEM;
  if (context?.portfolioValue) {
    systemWithContext += `\n\nPatrimônio atual do usuário: R$ ${context.portfolioValue.toLocaleString('pt-BR')}`;
  }
  if (context?.marketIndices) {
    systemWithContext += `\nMercado atual: SELIC ${context.marketIndices.selic}%, IPCA ${context.marketIndices.ipca}%, USD/BRL R$${context.marketIndices.usdBrl}`;
  }

  return callClaude(systemWithContext, message, history, apiKey);
}

/**
 * Generate market alerts based on current conditions
 */
export async function generateMarketAlerts(
  portfolio: { value: number; allocation: { ipcaPlus: number; posFixed: number; growth: number } },
  indices: MarketIndices,
  bonds: TesouroBond[],
): Promise<string[]> {
  const apiKey = await getClaudeApiKey();
  if (!apiKey) return [];

  const ipca35 = bonds.find(b => b.name.includes('2035'));
  const ipca45 = bonds.find(b => b.name.includes('2045'));

  const userMessage = `Gere de 2 a 4 alertas concisos (máx 1 linha cada) sobre o mercado atual para um investidor focado em atingir R$ 3M.

Dados:
- SELIC: ${indices.selic}% | IPCA: ${indices.ipca}% | USD/BRL: R$${indices.usdBrl}
- Ibovespa: ${indices.ibovespa.toLocaleString('pt-BR')} (${indices.ibovespaChange > 0 ? '+' : ''}${indices.ibovespaChange}%)
- Tesouro IPCA+ 2035: ${ipca35 ? `IPCA+${ipca35.annualRate}%` : 'N/D'}
- Tesouro IPCA+ 2045: ${ipca45 ? `IPCA+${ipca45.annualRate}%` : 'N/D'}
- Portfólio: IPCA+ ${portfolio.allocation.ipcaPlus}%, Pós-fixado ${portfolio.allocation.posFixed}%, Crescimento ${portfolio.allocation.growth}%

Formato: JSON array de strings. Apenas o array, sem markdown. Ex: ["Alerta 1", "Alerta 2"]`;

  try {
    const content = await callClaude(FINANCIAL_ADVISOR_SYSTEM, userMessage, [], apiKey);
    const cleaned = content.replace(/```json\n?|\n?```/g, '').trim();
    const alerts = JSON.parse(cleaned);
    return Array.isArray(alerts) ? alerts : [];
  } catch {
    return [];
  }
}
