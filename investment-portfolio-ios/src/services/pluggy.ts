import * as SecureStore from 'expo-secure-store';

const PLUGGY_API_URL = 'https://api.pluggy.ai';

export interface PluggyCredentials {
  clientId: string;
  clientSecret: string;
}

export interface PluggyAccount {
  id: string;
  itemId: string;
  name: string;
  number: string;
  balance: number;
  currencyCode: string;
  type: 'BANK' | 'CREDIT' | 'INVESTMENT';
  subtype?: string;
  institution?: string;
}

export interface PluggyTransaction {
  id: string;
  accountId: string;
  description: string;
  amount: number;
  date: string;
  type: 'DEBIT' | 'CREDIT';
  category?: string;
  balance?: number;
}

export interface PluggyInvestment {
  id: string;
  name: string;
  code: string;
  type: 'FIXED_INCOME' | 'EQUITY' | 'MUTUAL_FUND' | 'ETF' | 'REAL_ESTATE_FUND' | 'RETIREMENT';
  subtype?: string;
  balance: number;
  quantity?: number;
  unitPrice?: number;
  lastTransactionDate?: string;
  date: string;
  annualRate?: number;
  dueDate?: string;
}

export interface PluggyItem {
  id: string;
  status: 'UPDATED' | 'UPDATING' | 'WAITING_USER_INPUT' | 'LOGIN_ERROR' | 'ERROR';
  institutionId: number;
  institutionName: string;
  lastUpdatedAt?: string;
}

// ─── Credentials management ──────────────────────────────────────────────────

export async function savePluggyCredentials(creds: PluggyCredentials): Promise<void> {
  await SecureStore.setItemAsync('pluggy_client_id', creds.clientId);
  await SecureStore.setItemAsync('pluggy_client_secret', creds.clientSecret);
}

export async function getPluggyCredentials(): Promise<PluggyCredentials | null> {
  try {
    const clientId = await SecureStore.getItemAsync('pluggy_client_id');
    const clientSecret = await SecureStore.getItemAsync('pluggy_client_secret');

    if (!clientId || !clientSecret) return null;

    return { clientId, clientSecret };
  } catch {
    return null;
  }
}

// ─── Authentication ───────────────────────────────────────────────────────────

let cachedApiKey: string | null = null;
let apiKeyExpiry: number = 0;

async function getApiKey(): Promise<string | null> {
  const now = Date.now();

  // Return cached key if still valid (6 hours = 21600000ms, minus 5 min buffer)
  if (cachedApiKey && now < apiKeyExpiry - 300000) {
    return cachedApiKey;
  }

  const creds = await getPluggyCredentials();
  if (!creds) return null;

  try {
    const response = await fetch(`${PLUGGY_API_URL}/auth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clientId: creds.clientId, clientSecret: creds.clientSecret }),
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) throw new Error(`Auth error: ${response.status}`);

    const data = await response.json();
    cachedApiKey = data.apiKey;
    apiKeyExpiry = now + 21600000; // 6 hours

    return cachedApiKey;
  } catch (error) {
    console.error('Pluggy auth error:', error);
    return null;
  }
}

async function pluggyFetch(path: string): Promise<any> {
  const apiKey = await getApiKey();
  if (!apiKey) throw new Error('Pluggy não configurado. Configure suas credenciais em Configurações.');

  const response = await fetch(`${PLUGGY_API_URL}${path}`, {
    headers: { 'X-API-KEY': apiKey },
    signal: AbortSignal.timeout(15000),
  });

  if (!response.ok) {
    throw new Error(`Pluggy error ${response.status}: ${path}`);
  }

  return response.json();
}

// ─── Connect Widget token ────────────────────────────────────────────────────

export async function createConnectToken(itemId?: string): Promise<string> {
  const apiKey = await getApiKey();
  if (!apiKey) throw new Error('Pluggy não configurado');

  const body: Record<string, string> = {};
  if (itemId) body.itemId = itemId;

  const response = await fetch(`${PLUGGY_API_URL}/connect_token`, {
    method: 'POST',
    headers: { 'X-API-KEY': apiKey, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10000),
  });

  if (!response.ok) throw new Error('Falha ao criar token de conexão');

  const data = await response.json();
  return data.accessToken;
}

// ─── Items (connected institutions) ──────────────────────────────────────────

export async function getItems(): Promise<PluggyItem[]> {
  try {
    const data = await pluggyFetch('/items');
    return data.results || [];
  } catch {
    return [];
  }
}

export async function getItem(itemId: string): Promise<PluggyItem | null> {
  try {
    return await pluggyFetch(`/items/${itemId}`);
  } catch {
    return null;
  }
}

export async function deleteItem(itemId: string): Promise<void> {
  const apiKey = await getApiKey();
  if (!apiKey) return;

  await fetch(`${PLUGGY_API_URL}/items/${itemId}`, {
    method: 'DELETE',
    headers: { 'X-API-KEY': apiKey },
  });
}

// ─── Accounts ─────────────────────────────────────────────────────────────────

export async function getAccounts(itemId: string): Promise<PluggyAccount[]> {
  try {
    const data = await pluggyFetch(`/accounts?itemId=${itemId}`);
    return (data.results || []).map((acc: any): PluggyAccount => ({
      id: acc.id,
      itemId,
      name: acc.name,
      number: acc.number || '',
      balance: acc.balance || 0,
      currencyCode: acc.currencyCode || 'BRL',
      type: acc.type || 'BANK',
      subtype: acc.subtype,
      institution: acc.institution?.name,
    }));
  } catch {
    return [];
  }
}

export async function getAllAccounts(itemIds: string[]): Promise<PluggyAccount[]> {
  const allAccounts: PluggyAccount[] = [];
  for (const itemId of itemIds) {
    const accounts = await getAccounts(itemId);
    allAccounts.push(...accounts);
  }
  return allAccounts;
}

// ─── Transactions ────────────────────────────────────────────────────────────

export async function getTransactions(
  accountId: string,
  fromDate: string,
  toDate: string,
  limit: number = 100,
): Promise<PluggyTransaction[]> {
  try {
    const path = `/transactions?accountId=${accountId}&from=${fromDate}&to=${toDate}&pageSize=${limit}`;
    const data = await pluggyFetch(path);

    return (data.results || []).map((tx: any): PluggyTransaction => ({
      id: tx.id,
      accountId,
      description: tx.description || tx.descriptionRaw || '',
      amount: Math.abs(tx.amount || 0),
      date: tx.date,
      type: tx.type || (tx.amount < 0 ? 'DEBIT' : 'CREDIT'),
      category: tx.category,
      balance: tx.balance,
    }));
  } catch {
    return [];
  }
}

export async function getRecentTransactions(
  accountIds: string[],
  months: number = 3,
): Promise<PluggyTransaction[]> {
  const toDate = new Date().toISOString().split('T')[0];
  const fromDate = new Date(Date.now() - months * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const allTransactions: PluggyTransaction[] = [];
  for (const accountId of accountIds) {
    const txs = await getTransactions(accountId, fromDate, toDate, 200);
    allTransactions.push(...txs);
  }

  return allTransactions.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

// ─── Investments ──────────────────────────────────────────────────────────────

export async function getInvestments(itemId: string): Promise<PluggyInvestment[]> {
  try {
    const data = await pluggyFetch(`/investments?itemId=${itemId}`);

    return (data.results || []).map((inv: any): PluggyInvestment => ({
      id: inv.id,
      name: inv.name || inv.code || '',
      code: inv.code || '',
      type: inv.type || 'FIXED_INCOME',
      subtype: inv.subtype,
      balance: inv.balance || inv.value || 0,
      quantity: inv.quantity,
      unitPrice: inv.unitPrice,
      lastTransactionDate: inv.lastTransactionDate,
      date: inv.date,
      annualRate: inv.annualRate,
      dueDate: inv.dueDate,
    }));
  } catch {
    return [];
  }
}

export async function getAllInvestments(itemIds: string[]): Promise<PluggyInvestment[]> {
  const allInvestments: PluggyInvestment[] = [];
  for (const itemId of itemIds) {
    const investments = await getInvestments(itemId);
    allInvestments.push(...investments);
  }
  return allInvestments;
}

// ─── Summary ─────────────────────────────────────────────────────────────────

export interface FinancialSummary {
  totalBalance: number;           // sum of all bank accounts
  totalInvestments: number;       // sum of all investments
  totalNetWorth: number;          // balance + investments
  monthIncome: number;            // sum of CREDIT transactions this month
  monthExpenses: number;          // sum of DEBIT transactions this month
  monthBalance: number;           // income - expenses
  availableToInvest: number;      // month balance if positive
}

export function calculateSummary(
  accounts: PluggyAccount[],
  investments: PluggyInvestment[],
  transactions: PluggyTransaction[],
): FinancialSummary {
  const totalBalance = accounts
    .filter(a => a.type === 'BANK')
    .reduce((sum, a) => sum + a.balance, 0);

  const totalInvestments = investments.reduce((sum, i) => sum + i.balance, 0);

  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];

  const monthTransactions = transactions.filter(tx => tx.date >= monthStart);
  const monthIncome = monthTransactions
    .filter(tx => tx.type === 'CREDIT')
    .reduce((sum, tx) => sum + tx.amount, 0);
  const monthExpenses = monthTransactions
    .filter(tx => tx.type === 'DEBIT')
    .reduce((sum, tx) => sum + tx.amount, 0);

  const monthBalance = monthIncome - monthExpenses;

  return {
    totalBalance,
    totalInvestments,
    totalNetWorth: totalBalance + totalInvestments,
    monthIncome,
    monthExpenses,
    monthBalance,
    availableToInvest: Math.max(0, monthBalance),
  };
}

// ─── Institutions ────────────────────────────────────────────────────────────

export const SUPPORTED_INSTITUTIONS = [
  { id: 1, name: 'Itaú Unibanco', slug: 'itau', logo: '🏦', popular: true },
  { id: 2, name: 'Banco Bradesco', slug: 'bradesco', logo: '🏦', popular: true },
  { id: 3, name: 'Banco do Brasil', slug: 'bb', logo: '🏦', popular: true },
  { id: 4, name: 'Caixa Econômica Federal', slug: 'caixa', logo: '🏦', popular: true },
  { id: 5, name: 'Nubank', slug: 'nubank', logo: '💜', popular: true },
  { id: 6, name: 'BTG Pactual', slug: 'btg', logo: '📊', popular: true },
  { id: 7, name: 'XP Investimentos', slug: 'xp', logo: '📈', popular: true },
  { id: 8, name: 'Banco Inter', slug: 'inter', logo: '🟠', popular: true },
  { id: 9, name: 'Santander Brasil', slug: 'santander', logo: '🏦', popular: false },
  { id: 10, name: 'C6 Bank', slug: 'c6', logo: '🔷', popular: false },
];
