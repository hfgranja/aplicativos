// Market data service — integrates Brapi.dev and Tesouro Direto official API

export interface MarketQuote {
  ticker: string;
  name: string;
  price: number;
  change: number;         // absolute change
  changePercent: number;  // percentage change
  volume?: number;
  high?: number;
  low?: number;
  lastUpdate: Date;
}

export interface TesouroBond {
  id: string;
  name: string;
  type: 'SELIC' | 'IPCA' | 'Prefixado' | 'IPCARentabilidade';
  maturityDate: string;
  annualRate: number;       // rate spread (e.g., 5.5 for IPCA+5.5%)
  unitPrice: number;        // current buy price (BRL)
  minimumAmount: number;    // minimum investment
  indexer: 'SELIC' | 'IPCA' | 'Prefixado';
  lastUpdate: Date;
}

export interface MarketIndices {
  selic: number;        // annual %
  cdi: number;          // annual %
  ipca: number;         // last 12 months %
  usdBrl: number;       // USD/BRL exchange rate
  ibovespa: number;     // Ibovespa index value
  ibovespaChange: number; // % change
  lastUpdate: Date;
}

// Default tickers to track
export const DEFAULT_TICKERS = ['BOVA11', 'IVVB11', 'HGLG11', 'MXRF11', 'XPML11', 'PETR4', 'VALE3'];

/**
 * Fetch stock/ETF/FII quotes from Brapi.dev (free tier)
 * Docs: https://brapi.dev/docs
 */
export async function fetchQuotes(tickers: string[]): Promise<MarketQuote[]> {
  const tickerList = tickers.join(',');

  try {
    const response = await fetch(
      `https://brapi.dev/api/quote/${tickerList}?token=anonymous&fundamental=false`,
      { signal: AbortSignal.timeout(10000) }
    );

    if (!response.ok) {
      throw new Error(`Brapi.dev error: ${response.status}`);
    }

    const data = await response.json();
    const results = data?.results || [];

    return results.map((item: any): MarketQuote => ({
      ticker: item.symbol || '',
      name: item.longName || item.shortName || item.symbol || '',
      price: item.regularMarketPrice || 0,
      change: item.regularMarketChange || 0,
      changePercent: item.regularMarketChangePercent || 0,
      volume: item.regularMarketVolume,
      high: item.regularMarketDayHigh,
      low: item.regularMarketDayLow,
      lastUpdate: new Date(),
    }));
  } catch (error) {
    console.error('Error fetching quotes:', error);
    return getMockQuotes(tickers);
  }
}

/**
 * Fetch all available FIIs from Brapi.dev
 */
export async function fetchFIIList(): Promise<MarketQuote[]> {
  try {
    const response = await fetch(
      'https://brapi.dev/api/quote/list?type=fii&token=anonymous&limit=20&sortBy=dividendYield&sortOrder=desc',
      { signal: AbortSignal.timeout(10000) }
    );

    if (!response.ok) throw new Error(`FII list error: ${response.status}`);

    const data = await response.json();
    const stocks = data?.stocks || [];

    return stocks.slice(0, 20).map((item: any): MarketQuote => ({
      ticker: item.stock || '',
      name: item.name || '',
      price: item.close || 0,
      change: item.change || 0,
      changePercent: item.change || 0,
      lastUpdate: new Date(),
    }));
  } catch (error) {
    console.error('Error fetching FII list:', error);
    return [];
  }
}

/**
 * Fetch official Tesouro Direto bonds from the Treasury API
 * Official endpoint: https://www.tesourodireto.com.br/json/br/com/b3/tesouro/bond/search.json
 */
export async function fetchTesouroBonds(): Promise<TesouroBond[]> {
  try {
    const response = await fetch(
      'https://www.tesourodireto.com.br/json/br/com/b3/tesouro/bond/search.json',
      { signal: AbortSignal.timeout(15000) }
    );

    if (!response.ok) throw new Error(`Tesouro Direto error: ${response.status}`);

    const data = await response.json();
    const bonds = data?.response?.TrsrBdTradgList || [];

    return bonds.map((item: any): TesouroBond => {
      const bond = item.TrsrBd || {};
      const name: string = bond.nm || '';

      let type: TesouroBond['type'] = 'Prefixado';
      let indexer: TesouroBond['indexer'] = 'Prefixado';

      if (name.includes('IPCA+') && name.includes('Rend')) {
        type = 'IPCARentabilidade';
        indexer = 'IPCA';
      } else if (name.includes('IPCA+')) {
        type = 'IPCA';
        indexer = 'IPCA';
      } else if (name.includes('Selic') || name.includes('SELIC')) {
        type = 'SELIC';
        indexer = 'SELIC';
      }

      return {
        id: bond.cd?.toString() || name,
        name,
        type,
        maturityDate: bond.mtrtyDt || '',
        annualRate: parseFloat(bond.anulInvstmtRate || bond.anulRedRate || '0'),
        unitPrice: parseFloat(bond.untrInvstmtVal || '0'),
        minimumAmount: parseFloat(bond.minInvstmtAmt || '30'),
        indexer,
        lastUpdate: new Date(),
      };
    }).filter((b: TesouroBond) => b.unitPrice > 0);
  } catch (error) {
    console.error('Error fetching Tesouro Direto:', error);
    return getMockTesouroBonds();
  }
}

/**
 * Fetch market indices (CDI, SELIC, IPCA, USD/BRL) from HG Finance
 */
export async function fetchMarketIndices(): Promise<MarketIndices> {
  try {
    const response = await fetch(
      'https://api.hgbrasil.com/finance?format=json&fields=only_results,taxes,stocks',
      { signal: AbortSignal.timeout(10000) }
    );

    if (!response.ok) throw new Error(`HG Finance error: ${response.status}`);

    const data = await response.json();
    const results = data?.results || {};
    const taxes = results?.taxes || [];
    const stocks = results?.stocks || {};

    const selic = taxes.find((t: any) => t.name === 'Selic' || t.format?.includes('Selic'));
    const cdi = taxes.find((t: any) => t.name === 'CDI');
    const ipca = taxes.find((t: any) => t.name === 'IPCA' || t.name?.includes('IPCA'));

    const ibov = stocks?.IBOVESPA || {};

    return {
      selic: selic?.value || 13.75,
      cdi: cdi?.value || 13.65,
      ipca: ipca?.value || 4.83,
      usdBrl: results?.currencies?.USD?.buy || 5.0,
      ibovespa: ibov?.price || 130000,
      ibovespaChange: ibov?.change_percent || 0,
      lastUpdate: new Date(),
    };
  } catch (error) {
    console.error('Error fetching market indices:', error);
    return {
      selic: 13.75,
      cdi: 13.65,
      ipca: 4.83,
      usdBrl: 5.0,
      ibovespa: 130000,
      ibovespaChange: 0,
      lastUpdate: new Date(),
    };
  }
}

// ─── Mock data fallback ───────────────────────────────────────────────────────

function getMockQuotes(tickers: string[]): MarketQuote[] {
  const prices: Record<string, { name: string; price: number; change: number }> = {
    BOVA11: { name: 'iShares Ibovespa Fundo', price: 118.45, change: 0.8 },
    IVVB11: { name: 'iShares S&P 500 FIC FI', price: 310.20, change: 1.2 },
    HGLG11: { name: 'CSHG Logística FII', price: 162.80, change: -0.3 },
    MXRF11: { name: 'Maxi Renda FII', price: 10.85, change: 0.1 },
    XPML11: { name: 'XP Malls FII', price: 95.60, change: 0.5 },
    PETR4: { name: 'Petróleo Brasileiro PN', price: 38.25, change: 2.1 },
    VALE3: { name: 'Vale ON', price: 62.40, change: -1.5 },
  };

  return tickers.map(ticker => ({
    ticker,
    name: prices[ticker]?.name || ticker,
    price: prices[ticker]?.price || 100,
    change: prices[ticker]?.change || 0,
    changePercent: prices[ticker]?.change || 0,
    lastUpdate: new Date(),
  }));
}

function getMockTesouroBonds(): TesouroBond[] {
  return [
    {
      id: 'tesouro_ipca_2029',
      name: 'Tesouro IPCA+ 2029',
      type: 'IPCA',
      maturityDate: '2029-05-15',
      annualRate: 5.51,
      unitPrice: 3845.67,
      minimumAmount: 38.46,
      indexer: 'IPCA',
      lastUpdate: new Date(),
    },
    {
      id: 'tesouro_ipca_2035',
      name: 'Tesouro IPCA+ 2035',
      type: 'IPCA',
      maturityDate: '2035-05-15',
      annualRate: 5.75,
      unitPrice: 2543.21,
      minimumAmount: 25.44,
      indexer: 'IPCA',
      lastUpdate: new Date(),
    },
    {
      id: 'tesouro_ipca_2045',
      name: 'Tesouro IPCA+ 2045',
      type: 'IPCA',
      maturityDate: '2045-05-15',
      annualRate: 5.89,
      unitPrice: 1823.45,
      minimumAmount: 18.24,
      indexer: 'IPCA',
      lastUpdate: new Date(),
    },
    {
      id: 'tesouro_selic_2027',
      name: 'Tesouro Selic 2027',
      type: 'SELIC',
      maturityDate: '2027-03-01',
      annualRate: 0.0,
      unitPrice: 13456.78,
      minimumAmount: 134.57,
      indexer: 'SELIC',
      lastUpdate: new Date(),
    },
    {
      id: 'tesouro_selic_2029',
      name: 'Tesouro Selic 2029',
      type: 'SELIC',
      maturityDate: '2029-03-01',
      annualRate: 0.07,
      unitPrice: 14231.00,
      minimumAmount: 142.32,
      indexer: 'SELIC',
      lastUpdate: new Date(),
    },
    {
      id: 'tesouro_prefixado_2027',
      name: 'Tesouro Prefixado 2027',
      type: 'Prefixado',
      maturityDate: '2027-01-01',
      annualRate: 14.25,
      unitPrice: 823.45,
      minimumAmount: 8.24,
      indexer: 'Prefixado',
      lastUpdate: new Date(),
    },
  ];
}
