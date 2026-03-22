import { create } from 'zustand';
import { MarketQuote, TesouroBond, MarketIndices, fetchQuotes, fetchTesouroBonds, fetchMarketIndices, DEFAULT_TICKERS } from '../services/marketData';
import { PluggyAccount, PluggyTransaction, PluggyInvestment, getAllAccounts, getAllInvestments, getRecentTransactions, calculateSummary, FinancialSummary, getItems } from '../services/pluggy';
import { SimulatedPosition } from '../services/tradingSimulator';
import { AISuggestion, ChatMessage } from '../services/claudeAI';
import { DEFAULT_PLAN } from '../constants/scenarios';
import { InvestmentCategory } from '../constants/investments';

export interface AllocationConfig {
  ipcaPlus: number;
  posFixed: number;
  growth: number;
}

export interface PortfolioState {
  // Plan configuration
  monthlyContribution: number;
  annualContribution: number;
  extraAnnualContribution: number;
  goal: number;
  selectedScenario: string;

  // Market data
  marketQuotes: Record<string, MarketQuote>;
  tesouroBonds: TesouroBond[];
  marketIndices: MarketIndices | null;
  lastMarketUpdate: Date | null;
  isLoadingMarket: boolean;
  marketError: string | null;

  // Portfolio allocation
  allocation: AllocationConfig;

  // Paper trading positions
  paperPositions: SimulatedPosition[];
  cashBalance: number;

  // Open Finance data (Pluggy)
  pluggyItemIds: string[];
  bankAccounts: PluggyAccount[];
  realInvestments: PluggyInvestment[];
  transactions: PluggyTransaction[];
  financialSummary: FinancialSummary | null;
  isLoadingOpenFinance: boolean;
  openFinanceError: string | null;
  lastOpenFinanceUpdate: Date | null;

  // AI
  aiSuggestions: AISuggestion[];
  chatHistory: ChatMessage[];
  isLoadingAI: boolean;

  // Market alerts
  marketAlerts: string[];

  // Actions
  setContributions(monthly: number, annual: number, extra?: number): void;
  setAllocation(allocation: AllocationConfig): void;
  setSelectedScenario(scenarioId: string): void;
  addPaperPosition(position: SimulatedPosition): void;
  removePaperPosition(positionId: string): void;
  updatePaperPositions(positions: SimulatedPosition[]): void;
  addPluggyItem(itemId: string): void;
  removePluggyItem(itemId: string): void;
  refreshMarketData(): Promise<void>;
  refreshOpenFinance(): Promise<void>;
  addAISuggestion(suggestion: AISuggestion): void;
  addChatMessage(message: ChatMessage): void;
  clearChatHistory(): void;
  setMarketAlerts(alerts: string[]): void;
}

export const usePortfolioStore = create<PortfolioState>((set, get) => ({
  // Plan defaults (from the user's investment plan)
  monthlyContribution: DEFAULT_PLAN.monthlyContribution,
  annualContribution: DEFAULT_PLAN.annualContribution,
  extraAnnualContribution: 0,
  goal: DEFAULT_PLAN.goal,
  selectedScenario: 'base',

  // Market data
  marketQuotes: {},
  tesouroBonds: [],
  marketIndices: null,
  lastMarketUpdate: null,
  isLoadingMarket: false,
  marketError: null,

  // Portfolio allocation (recommended split from the plan)
  allocation: {
    ipcaPlus: 55,
    posFixed: 25,
    growth: 20,
  },

  // Paper trading
  paperPositions: [],
  cashBalance: 0,

  // Open Finance
  pluggyItemIds: [],
  bankAccounts: [],
  realInvestments: [],
  transactions: [],
  financialSummary: null,
  isLoadingOpenFinance: false,
  openFinanceError: null,
  lastOpenFinanceUpdate: null,

  // AI
  aiSuggestions: [],
  chatHistory: [],
  isLoadingAI: false,
  marketAlerts: [],

  // ─── Actions ─────────────────────────────────────────────────────────────

  setContributions(monthly, annual, extra = 0) {
    set({ monthlyContribution: monthly, annualContribution: annual, extraAnnualContribution: extra });
  },

  setAllocation(allocation) {
    // Normalize so that sum = 100
    const total = allocation.ipcaPlus + allocation.posFixed + allocation.growth;
    if (total === 0) return;
    set({
      allocation: {
        ipcaPlus: Math.round((allocation.ipcaPlus / total) * 100),
        posFixed: Math.round((allocation.posFixed / total) * 100),
        growth: Math.round((allocation.growth / total) * 100),
      },
    });
  },

  setSelectedScenario(scenarioId) {
    set({ selectedScenario: scenarioId });
  },

  addPaperPosition(position) {
    set(state => ({ paperPositions: [...state.paperPositions, position] }));
  },

  removePaperPosition(positionId) {
    set(state => ({
      paperPositions: state.paperPositions.filter(p => p.id !== positionId),
    }));
  },

  updatePaperPositions(positions) {
    set({ paperPositions: positions });
  },

  addPluggyItem(itemId) {
    set(state => ({
      pluggyItemIds: state.pluggyItemIds.includes(itemId)
        ? state.pluggyItemIds
        : [...state.pluggyItemIds, itemId],
    }));
  },

  removePluggyItem(itemId) {
    set(state => ({
      pluggyItemIds: state.pluggyItemIds.filter(id => id !== itemId),
    }));
  },

  async refreshMarketData() {
    set({ isLoadingMarket: true, marketError: null });

    try {
      const [quotes, bonds, indices] = await Promise.all([
        fetchQuotes(DEFAULT_TICKERS),
        fetchTesouroBonds(),
        fetchMarketIndices(),
      ]);

      const quotesMap: Record<string, MarketQuote> = {};
      for (const q of quotes) {
        quotesMap[q.ticker] = q;
      }

      set({
        marketQuotes: quotesMap,
        tesouroBonds: bonds,
        marketIndices: indices,
        lastMarketUpdate: new Date(),
        isLoadingMarket: false,
      });
    } catch (error) {
      set({
        isLoadingMarket: false,
        marketError: error instanceof Error ? error.message : 'Erro ao carregar dados do mercado',
      });
    }
  },

  async refreshOpenFinance() {
    const { pluggyItemIds } = get();
    if (pluggyItemIds.length === 0) return;

    set({ isLoadingOpenFinance: true, openFinanceError: null });

    try {
      const [accounts, investments] = await Promise.all([
        getAllAccounts(pluggyItemIds),
        getAllInvestments(pluggyItemIds),
      ]);

      const bankAccountIds = accounts.filter(a => a.type === 'BANK').map(a => a.id);
      const transactions = await getRecentTransactions(bankAccountIds, 3);

      const summary = calculateSummary(accounts, investments, transactions);

      set({
        bankAccounts: accounts,
        realInvestments: investments,
        transactions,
        financialSummary: summary,
        lastOpenFinanceUpdate: new Date(),
        isLoadingOpenFinance: false,
      });
    } catch (error) {
      set({
        isLoadingOpenFinance: false,
        openFinanceError: error instanceof Error ? error.message : 'Erro ao carregar dados bancários',
      });
    }
  },

  addAISuggestion(suggestion) {
    set(state => ({
      aiSuggestions: [suggestion, ...state.aiSuggestions].slice(0, 20),
    }));
  },

  addChatMessage(message) {
    set(state => ({
      chatHistory: [...state.chatHistory, message].slice(-50),
    }));
  },

  clearChatHistory() {
    set({ chatHistory: [] });
  },

  setMarketAlerts(alerts) {
    set({ marketAlerts: alerts });
  },
}));

// Computed selectors (derived state)
export function selectTotalPortfolioValue(state: PortfolioState): number {
  const paperValue = state.paperPositions.reduce(
    (sum, pos) => sum + pos.currentPrice * pos.quantity,
    0,
  );
  const realInvestmentsValue = state.realInvestments.reduce(
    (sum, inv) => sum + inv.balance,
    0,
  );
  return paperValue + realInvestmentsValue;
}

export function selectTotalNetWorth(state: PortfolioState): number {
  return (state.financialSummary?.totalNetWorth || 0) + selectTotalPortfolioValue(state);
}
