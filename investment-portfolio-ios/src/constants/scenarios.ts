import { Colors } from './colors';

export interface Scenario {
  id: string;
  label: string;
  shortLabel: string;
  realRate: number;      // Annual real return (inflation-adjusted)
  color: string;
  description: string;
  yearsToGoal?: number;  // Calculated dynamically
}

export const SCENARIOS: Scenario[] = [
  {
    id: 'conservative',
    label: 'Conservador',
    shortLabel: 'Conserv.',
    realRate: 0.02,
    color: Colors.scenarioConservative,
    description: '2% a.a. real — Tesouro SELIC, LCI/LCA, CDB CDI. Menor risco, menor retorno.',
  },
  {
    id: 'base',
    label: 'Base',
    shortLabel: 'Base',
    realRate: 0.04,
    color: Colors.scenarioBase,
    description: '4% a.a. real — Mix IPCA+ e pós-fixado. Carteira equilibrada.',
  },
  {
    id: 'aggressive',
    label: 'Arrojado',
    shortLabel: 'Arrojado',
    realRate: 0.06,
    color: Colors.scenarioAggressive,
    description: '6% a.a. real — IPCA+, FIIs, ETFs. Plausível com disciplina e diversificação.',
  },
  {
    id: 'veryStrong',
    label: 'Muito Forte',
    shortLabel: 'Forte',
    realRate: 0.08,
    color: Colors.scenarioVeryStrong,
    description: '8% a.a. real — Carteira agressiva com ações, ETFs e IPCA+. Requer tolerância a volatilidade.',
  },
];

export const DEFAULT_PLAN = {
  monthlyContribution: 1000,
  annualContribution: 200000,
  goal: 3000000,
  initialValue: 0,
};

export const MILESTONES = [1000000, 2000000, 3000000];
