import { fetchQuotes } from './marketData';
import { InvestmentCategory } from '../constants/investments';

export interface SimulatedPosition {
  id: string;
  ticker: string;
  name: string;
  category: InvestmentCategory;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  purchaseDate: string;
  type: 'stock' | 'fii' | 'etf' | 'tesouro' | 'cdb' | 'lci' | 'lca';
}

export interface TradeResult {
  positionId: string;
  ticker: string;
  type: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  totalValue: number;
  date: string;
  pnl?: number;     // profit/loss for sells
  pnlPct?: number;  // P&L percentage for sells
}

export interface PnLSummary {
  totalInvested: number;
  currentValue: number;
  totalPnL: number;
  totalPnLPct: number;
  positions: Array<{
    positionId: string;
    ticker: string;
    invested: number;
    currentValue: number;
    pnl: number;
    pnlPct: number;
  }>;
}

/**
 * Simulate buying a position with current market price
 */
export async function simulateBuy(
  ticker: string,
  name: string,
  amount: number,
  category: InvestmentCategory,
  type: SimulatedPosition['type'],
): Promise<SimulatedPosition> {
  const quotes = await fetchQuotes([ticker]);
  const quote = quotes[0];

  if (!quote || quote.price === 0) {
    throw new Error(`Cotação não disponível para ${ticker}`);
  }

  const price = quote.price;
  const quantity = Math.floor(amount / price);

  if (quantity === 0) {
    throw new Error(`Valor insuficiente. Mínimo: R$ ${price.toFixed(2)} para 1 cota de ${ticker}`);
  }

  return {
    id: `pos_${Date.now()}_${ticker}`,
    ticker,
    name,
    category,
    quantity,
    avgPrice: price,
    currentPrice: price,
    purchaseDate: new Date().toISOString().split('T')[0],
    type,
  };
}

/**
 * Simulate selling a position
 */
export async function simulateSell(
  position: SimulatedPosition,
  quantityToSell: number,
): Promise<TradeResult> {
  const quotes = await fetchQuotes([position.ticker]);
  const quote = quotes[0];

  const currentPrice = quote?.price || position.currentPrice;
  const totalValue = currentPrice * quantityToSell;
  const invested = position.avgPrice * quantityToSell;
  const pnl = totalValue - invested;
  const pnlPct = invested > 0 ? (pnl / invested) * 100 : 0;

  return {
    positionId: position.id,
    ticker: position.ticker,
    type: 'SELL',
    quantity: quantityToSell,
    price: currentPrice,
    totalValue,
    date: new Date().toISOString().split('T')[0],
    pnl,
    pnlPct,
  };
}

/**
 * Update current prices of all positions
 */
export async function updatePositionPrices(
  positions: SimulatedPosition[],
): Promise<SimulatedPosition[]> {
  const tickers = [...new Set(positions.map(p => p.ticker))];
  const quotes = await fetchQuotes(tickers);

  const priceMap: Record<string, number> = {};
  for (const quote of quotes) {
    priceMap[quote.ticker] = quote.price;
  }

  return positions.map(pos => ({
    ...pos,
    currentPrice: priceMap[pos.ticker] || pos.currentPrice,
  }));
}

/**
 * Calculate P&L for all positions
 */
export function calculatePortfolioPnL(positions: SimulatedPosition[]): PnLSummary {
  let totalInvested = 0;
  let currentValue = 0;

  const positionPnL = positions.map(pos => {
    const invested = pos.avgPrice * pos.quantity;
    const value = pos.currentPrice * pos.quantity;
    const pnl = value - invested;
    const pnlPct = invested > 0 ? (pnl / invested) * 100 : 0;

    totalInvested += invested;
    currentValue += value;

    return {
      positionId: pos.id,
      ticker: pos.ticker,
      invested,
      currentValue: value,
      pnl,
      pnlPct,
    };
  });

  const totalPnL = currentValue - totalInvested;
  const totalPnLPct = totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0;

  return {
    totalInvested,
    currentValue,
    totalPnL,
    totalPnLPct,
    positions: positionPnL,
  };
}

/**
 * Get current value of a position
 */
export function getPositionValue(position: SimulatedPosition): number {
  return position.currentPrice * position.quantity;
}

/**
 * Get P&L for a single position
 */
export function getPositionPnL(position: SimulatedPosition): { pnl: number; pnlPct: number } {
  const invested = position.avgPrice * position.quantity;
  const current = position.currentPrice * position.quantity;
  const pnl = current - invested;
  const pnlPct = invested > 0 ? (pnl / invested) * 100 : 0;
  return { pnl, pnlPct };
}

/**
 * Check IR rules for stock sales (isenção < R$20k/mês)
 */
export function checkStockSaleIRRule(
  monthlyStockSales: number,
): { isExempt: boolean; warningLevel: 'safe' | 'warning' | 'taxable'; message: string } {
  const EXEMPTION_LIMIT = 20000;

  if (monthlyStockSales === 0) {
    return {
      isExempt: true,
      warningLevel: 'safe',
      message: 'Nenhuma venda de ações este mês.',
    };
  }

  if (monthlyStockSales < EXEMPTION_LIMIT * 0.8) {
    return {
      isExempt: true,
      warningLevel: 'safe',
      message: `Vendas no mês: R$ ${monthlyStockSales.toLocaleString('pt-BR')} — dentro do limite de isenção (R$ 20k).`,
    };
  }

  if (monthlyStockSales < EXEMPTION_LIMIT) {
    const remaining = EXEMPTION_LIMIT - monthlyStockSales;
    return {
      isExempt: true,
      warningLevel: 'warning',
      message: `Atenção! Vendas: R$ ${monthlyStockSales.toLocaleString('pt-BR')}. Restam R$ ${remaining.toLocaleString('pt-BR')} para o limite de isenção de R$ 20k.`,
    };
  }

  const excess = monthlyStockSales - EXEMPTION_LIMIT;
  const irDue = excess * 0.15;
  return {
    isExempt: false,
    warningLevel: 'taxable',
    message: `IR devido! Vendas: R$ ${monthlyStockSales.toLocaleString('pt-BR')} (excedeu R$ 20k). IR estimado: R$ ${irDue.toLocaleString('pt-BR')} (15% sobre R$ ${excess.toLocaleString('pt-BR')}). Pague via DARF até o último dia útil do mês seguinte.`,
  };
}
