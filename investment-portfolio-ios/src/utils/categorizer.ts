export type ExpenseCategory =
  | 'alimentacao'
  | 'moradia'
  | 'transporte'
  | 'saude'
  | 'educacao'
  | 'lazer'
  | 'vestuario'
  | 'financeiro'
  | 'salario'
  | 'investimento'
  | 'outros';

export interface CategoryInfo {
  id: ExpenseCategory;
  label: string;
  icon: string;
  color: string;
  dedutiveIR: boolean;
  irNote?: string;
}

export const EXPENSE_CATEGORIES: Record<ExpenseCategory, CategoryInfo> = {
  alimentacao: {
    id: 'alimentacao',
    label: 'Alimentação',
    icon: '🍽️',
    color: '#f59e0b',
    dedutiveIR: false,
  },
  moradia: {
    id: 'moradia',
    label: 'Moradia',
    icon: '🏠',
    color: '#6366f1',
    dedutiveIR: false,
  },
  transporte: {
    id: 'transporte',
    label: 'Transporte',
    icon: '🚗',
    color: '#3b82f6',
    dedutiveIR: false,
  },
  saude: {
    id: 'saude',
    label: 'Saúde',
    icon: '🏥',
    color: '#ef4444',
    dedutiveIR: true,
    irNote: 'Médicos, dentistas, psicólogos e hospitais são dedutíveis sem limite no IR (modelo completo).',
  },
  educacao: {
    id: 'educacao',
    label: 'Educação',
    icon: '📚',
    color: '#8b5cf6',
    dedutiveIR: true,
    irNote: 'Dedutível até R$ 3.561,50/ano por dependente no IR.',
  },
  lazer: {
    id: 'lazer',
    label: 'Lazer',
    icon: '🎮',
    color: '#10b981',
    dedutiveIR: false,
  },
  vestuario: {
    id: 'vestuario',
    label: 'Vestuário',
    icon: '👕',
    color: '#ec4899',
    dedutiveIR: false,
  },
  financeiro: {
    id: 'financeiro',
    label: 'Financeiro',
    icon: '💳',
    color: '#64748b',
    dedutiveIR: false,
  },
  salario: {
    id: 'salario',
    label: 'Salário / Renda',
    icon: '💰',
    color: '#22c55e',
    dedutiveIR: false,
  },
  investimento: {
    id: 'investimento',
    label: 'Investimento',
    icon: '📈',
    color: '#6366f1',
    dedutiveIR: false,
  },
  outros: {
    id: 'outros',
    label: 'Outros',
    icon: '📦',
    color: '#94a3b8',
    dedutiveIR: false,
  },
};

// Keywords for automatic transaction categorization
const CATEGORY_KEYWORDS: Record<ExpenseCategory, string[]> = {
  alimentacao: [
    'restaurante', 'lanche', 'ifood', 'rappi', 'uber eats', 'mcdonalds', 'burger',
    'pizza', 'padaria', 'supermercado', 'mercado', 'extra', 'carrefour', 'pao de acucar',
    'big box', 'atacadao', 'assai', 'hortifruti', 'açougue', 'delicia', 'cafe', 'bar',
  ],
  moradia: [
    'aluguel', 'condominio', 'iptu', 'energia', 'enel', 'luz', 'agua', 'sabesp',
    'caesb', 'embasa', 'gás', 'net', 'claro', 'internet', 'tim', 'vivo', 'oi',
    'seguro residencial', 'mobilia', 'casas bahia', 'magazine luiza', 'americanas',
  ],
  transporte: [
    'uber', '99', 'cabify', 'taxi', 'combustivel', 'gasolina', 'etanol', 'diesel',
    'ipva', 'seguro auto', 'estacionamento', 'pedagio', 'metro', 'trem', 'onibus',
    'passagem', 'azul', 'gol', 'latam', 'tam', 'fletx', 'buser',
  ],
  saude: [
    'farmacia', 'drogasil', 'ultrafarma', 'pacheco', 'raia', 'clinica', 'hospital',
    'consultorio', 'medico', 'dentista', 'psicologo', 'plano saude', 'unimed',
    'hapvida', 'bradesco saude', 'amil', 'sulamerica saude', 'academia',
  ],
  educacao: [
    'escola', 'faculdade', 'universidade', 'curso', 'mensalidade', 'material escolar',
    'livro', 'udemy', 'coursera', 'alura', 'descomplica', 'cursinho',
  ],
  lazer: [
    'cinema', 'teatro', 'show', 'netflix', 'spotify', 'amazon prime', 'disney',
    'hbo', 'globoplay', 'youtube premium', 'steam', 'playstation', 'xbox',
    'viagem', 'hotel', 'airbnb', 'ingresso', 'parque', 'jogos',
  ],
  vestuario: [
    'zara', 'hm', 'renner', 'riachuelo', 'c&a', 'marisa', 'totvs', 'nike', 'adidas',
    'havaianas', 'arezzo', 'moda', 'roupa', 'calcado', 'sapato', 'tenis',
  ],
  financeiro: [
    'tarifa', 'taxa', 'juros', 'anuidade', 'fatura', 'parcela', 'emprestimo',
    'financiamento', 'seguro', 'ted', 'doc', 'pix', 'banco',
  ],
  salario: [
    'salario', 'pagamento', 'holerite', 'plr', 'bonus', 'comissao', 'prolabore',
    'honorario', 'dividendo recebido', 'rendimento',
  ],
  investimento: [
    'tesouro', 'cdb', 'lci', 'lca', 'aplicacao', 'resgate', 'fii', 'acao', 'etf',
    'fundo', 'previdencia', 'pgbl', 'vgbl', 'bolsa', 'b3', 'xp', 'btg', 'nuinvest',
    'rico', 'clear', 'modal', 'inter invest',
  ],
  outros: [],
};

/**
 * Categorize a transaction description automatically
 */
export function categorizeTransaction(description: string): ExpenseCategory {
  const lower = description.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    if (category === 'outros') continue;
    for (const keyword of keywords) {
      const normalizedKeyword = keyword.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      if (lower.includes(normalizedKeyword)) {
        return category as ExpenseCategory;
      }
    }
  }

  return 'outros';
}

/**
 * Group transactions by category and sum amounts
 */
export interface CategorySummary {
  category: ExpenseCategory;
  info: CategoryInfo;
  total: number;
  count: number;
  percentage: number;
}

export function summarizeByCategory(
  transactions: Array<{ description: string; amount: number; type: 'DEBIT' | 'CREDIT' }>,
): CategorySummary[] {
  const totals: Record<ExpenseCategory, { total: number; count: number }> = {} as any;

  for (const tx of transactions) {
    if (tx.type !== 'DEBIT') continue;
    const cat = categorizeTransaction(tx.description);
    if (!totals[cat]) totals[cat] = { total: 0, count: 0 };
    totals[cat].total += Math.abs(tx.amount);
    totals[cat].count += 1;
  }

  const grandTotal = Object.values(totals).reduce((sum, { total }) => sum + total, 0);

  return Object.entries(totals)
    .map(([category, { total, count }]) => ({
      category: category as ExpenseCategory,
      info: EXPENSE_CATEGORIES[category as ExpenseCategory],
      total,
      count,
      percentage: grandTotal > 0 ? (total / grandTotal) * 100 : 0,
    }))
    .sort((a, b) => b.total - a.total);
}

/**
 * Detect potentially IR-deductible transactions
 */
export function detectDeductibleExpenses(
  transactions: Array<{ description: string; amount: number; date: string }>,
): Array<{ description: string; amount: number; date: string; category: ExpenseCategory; irNote: string }> {
  return transactions
    .filter(tx => {
      const cat = categorizeTransaction(tx.description);
      return EXPENSE_CATEGORIES[cat].dedutiveIR;
    })
    .map(tx => {
      const cat = categorizeTransaction(tx.description);
      return {
        ...tx,
        category: cat,
        irNote: EXPENSE_CATEGORIES[cat].irNote || '',
      };
    });
}
