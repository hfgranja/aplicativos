import { SCENARIOS, MILESTONES } from '../constants/scenarios';

export interface YearlySnapshot {
  year: number;
  value: number;
}

export interface ProjectionParams {
  initialValue?: number;
  monthlyContribution: number;
  annualLumpSum: number;
  extraAnnualContribution?: number;
  annualRealRate: number;
  years: number;
}

export interface MilestoneResult {
  target: number;
  label: string;
  years: number | null;  // null = never reached in projection
  scenarioId: string;
}

export interface ScenarioProjection {
  scenarioId: string;
  label: string;
  color: string;
  data: YearlySnapshot[];
  yearsToGoal: number | null;
}

/**
 * Projects portfolio growth month by month.
 * Annual lump sum is deposited at the start of each year (month 1 of each year)
 * for maximum compounding effect — as specified in the plan.
 */
export function projectPortfolio(params: ProjectionParams): YearlySnapshot[] {
  const {
    initialValue = 0,
    monthlyContribution,
    annualLumpSum,
    extraAnnualContribution = 0,
    annualRealRate,
    years,
  } = params;

  const monthlyRate = Math.pow(1 + annualRealRate, 1 / 12) - 1;
  const totalAnnualLump = annualLumpSum + extraAnnualContribution;

  let balance = initialValue;
  const snapshots: YearlySnapshot[] = [{ year: 0, value: balance }];

  for (let month = 1; month <= years * 12; month++) {
    // Annual lump sum deposited at start of each year
    if (month % 12 === 1) {
      balance += totalAnnualLump;
    }

    // Monthly contribution at end of each month
    balance += monthlyContribution;

    // Apply monthly interest
    balance *= 1 + monthlyRate;

    // Take yearly snapshot
    if (month % 12 === 0) {
      snapshots.push({ year: month / 12, value: Math.round(balance) });
    }
  }

  return snapshots;
}

/**
 * Calculate years to reach a goal (returns fractional years, or null if not reached in 50 years)
 */
export function yearsToGoal(params: Omit<ProjectionParams, 'years'> & { goal: number }): number | null {
  const { goal, ...projParams } = params;
  const monthlyRate = Math.pow(1 + projParams.annualRealRate, 1 / 12) - 1;
  const totalAnnualLump = projParams.annualLumpSum + (projParams.extraAnnualContribution || 0);

  let balance = projParams.initialValue || 0;

  for (let month = 1; month <= 50 * 12; month++) {
    if (month % 12 === 1) {
      balance += totalAnnualLump;
    }
    balance += projParams.monthlyContribution;
    balance *= 1 + monthlyRate;

    if (balance >= goal) {
      return month / 12;
    }
  }

  return null;
}

/**
 * Calculate all scenario projections for the chart
 */
export function getAllScenarioProjections(params: Omit<ProjectionParams, 'annualRealRate'>): ScenarioProjection[] {
  return SCENARIOS.map(scenario => {
    const data = projectPortfolio({ ...params, annualRealRate: scenario.realRate });
    const ytg = yearsToGoal({ ...params, annualRealRate: scenario.realRate, goal: 3_000_000 });

    return {
      scenarioId: scenario.id,
      label: scenario.label,
      color: scenario.color,
      data,
      yearsToGoal: ytg,
    };
  });
}

/**
 * Calculate when each scenario hits each milestone (R$1M, R$2M, R$3M)
 */
export function calculateMilestones(params: Omit<ProjectionParams, 'annualRealRate'>): MilestoneResult[] {
  const results: MilestoneResult[] = [];

  for (const scenario of SCENARIOS) {
    for (const target of MILESTONES) {
      const years = yearsToGoal({
        ...params,
        annualRealRate: scenario.realRate,
        goal: target,
      });

      results.push({
        target,
        label: `R$ ${(target / 1_000_000).toFixed(0)}M`,
        years: years !== null ? Math.round(years * 10) / 10 : null,
        scenarioId: scenario.id,
      });
    }
  }

  return results;
}

/**
 * Calculate the impact of an extra annual contribution
 */
export function extraContributionImpact(
  baseParams: Omit<ProjectionParams, 'annualRealRate'>,
  extraAmount: number,
  annualRealRate: number = 0.04, // default base scenario
  goal: number = 3_000_000,
): { yearsReduced: number; finalValueAt20Years: number } {
  const baseYears = yearsToGoal({ ...baseParams, annualRealRate, goal });
  const newYears = yearsToGoal({
    ...baseParams,
    extraAnnualContribution: (baseParams.extraAnnualContribution || 0) + extraAmount,
    annualRealRate,
    goal,
  });

  const baseAt20 = projectPortfolio({ ...baseParams, annualRealRate, years: 20 });
  const newAt20 = projectPortfolio({
    ...baseParams,
    extraAnnualContribution: (baseParams.extraAnnualContribution || 0) + extraAmount,
    annualRealRate,
    years: 20,
  });

  const yearsReduced = baseYears !== null && newYears !== null
    ? Math.round((baseYears - newYears) * 10) / 10
    : 0;

  return {
    yearsReduced,
    finalValueAt20Years: newAt20[newAt20.length - 1]?.value ?? 0,
  };
}

/**
 * Total annual contribution
 */
export function totalAnnualContribution(monthly: number, annual: number, extra: number = 0): number {
  return monthly * 12 + annual + extra;
}

/**
 * Format a currency value for display
 */
export function formatBRL(value: number): string {
  if (value >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(2)}M`;
  }
  if (value >= 1_000) {
    return `R$ ${(value / 1_000).toFixed(1)}k`;
  }
  return `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function formatBRLFull(value: number): string {
  return `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Goal completion percentage
 */
export function goalProgress(currentValue: number, goal: number): number {
  return Math.min(100, (currentValue / goal) * 100);
}
