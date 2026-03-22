import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TextInput, TouchableOpacity, Dimensions,
} from 'react-native';
import { LineChart } from 'victory-native';
import { usePortfolioStore } from '../../src/store/usePortfolioStore';
import {
  getAllScenarioProjections,
  calculateMilestones,
  formatBRL,
  formatBRLFull,
} from '../../src/utils/calculations';
import { Card, SectionHeader, PillButton } from '../../src/components/shared';
import { Colors, Spacing, FontSize } from '../../src/constants/colors';
import { SCENARIOS, MILESTONES } from '../../src/constants/scenarios';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function ProjectionsScreen() {
  const store = usePortfolioStore();
  const { monthlyContribution, annualContribution, extraAnnualContribution } = store;

  const [activeScenarios, setActiveScenarios] = useState<Record<string, boolean>>({
    conservative: true,
    base: true,
    aggressive: true,
    veryStrong: true,
  });

  const [localMonthly, setLocalMonthly] = useState(monthlyContribution.toString());
  const [localAnnual, setLocalAnnual] = useState(annualContribution.toString());
  const [localExtra, setLocalExtra] = useState(extraAnnualContribution.toString());

  const monthly = parseInt(localMonthly.replace(/\D/g, ''), 10) || 0;
  const annual = parseInt(localAnnual.replace(/\D/g, ''), 10) || 0;
  const extra = parseInt(localExtra.replace(/\D/g, ''), 10) || 0;

  const projections = getAllScenarioProjections({
    initialValue: 0,
    monthlyContribution: monthly,
    annualLumpSum: annual,
    extraAnnualContribution: extra,
    years: 20,
  });

  const milestones = calculateMilestones({
    monthlyContribution: monthly,
    annualLumpSum: annual,
    extraAnnualContribution: extra,
    years: 20,
  });

  const toggleScenario = (id: string) => {
    setActiveScenarios(prev => {
      const next = { ...prev, [id]: !prev[id] };
      const anyActive = Object.values(next).some(Boolean);
      if (!anyActive) return prev;
      return next;
    });
  };

  const chartData = projections[0]?.data.map((_, i) => ({
    year: projections[0].data[i].year,
    conservative: activeScenarios.conservative ? projections.find(p => p.scenarioId === 'conservative')?.data[i]?.value || 0 : undefined,
    base: activeScenarios.base ? projections.find(p => p.scenarioId === 'base')?.data[i]?.value || 0 : undefined,
    aggressive: activeScenarios.aggressive ? projections.find(p => p.scenarioId === 'aggressive')?.data[i]?.value || 0 : undefined,
    veryStrong: activeScenarios.veryStrong ? projections.find(p => p.scenarioId === 'veryStrong')?.data[i]?.value || 0 : undefined,
  })).filter((d): d is typeof d & { year: number } => d !== undefined) || [];

  const activeKeys = Object.entries(activeScenarios)
    .filter(([, active]) => active)
    .map(([id]) => id as 'conservative' | 'base' | 'aggressive' | 'veryStrong');

  const activeColors = activeKeys.map(id => SCENARIOS.find(s => s.id === id)?.color || '#fff');

  const milestoneSummary = MILESTONES.map(target => ({
    target,
    label: `R$ ${(target / 1_000_000).toFixed(0)}M`,
    byScenario: SCENARIOS.map(s => {
      const m = milestones.find(m => m.target === target && m.scenarioId === s.id);
      return { scenario: s, years: m?.years || null };
    }),
  }));

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Projeções</Text>
        <Text style={styles.headerSubtitle}>Retornos reais (já descontada a inflação)</Text>
      </View>

      {/* Contribution Inputs */}
      <Card style={styles.inputCard}>
        <SectionHeader title="Configurar Aportes" />
        <View style={styles.inputsRow}>
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Mensal</Text>
            <TextInput
              style={styles.input}
              value={localMonthly}
              onChangeText={setLocalMonthly}
              keyboardType="numeric"
              placeholder="1000"
              placeholderTextColor={Colors.textMuted}
            />
          </View>
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Anual</Text>
            <TextInput
              style={styles.input}
              value={localAnnual}
              onChangeText={setLocalAnnual}
              keyboardType="numeric"
              placeholder="200000"
              placeholderTextColor={Colors.textMuted}
            />
          </View>
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Extra/ano</Text>
            <TextInput
              style={styles.input}
              value={localExtra}
              onChangeText={setLocalExtra}
              keyboardType="numeric"
              placeholder="0"
              placeholderTextColor={Colors.textMuted}
            />
          </View>
        </View>
        <Text style={styles.inputTotal}>
          Total anual: {formatBRL(monthly * 12 + annual + extra)}
        </Text>
      </Card>

      {/* Scenario Toggles */}
      <View style={styles.scenarioToggles}>
        {SCENARIOS.map(scenario => (
          <PillButton
            key={scenario.id}
            label={scenario.shortLabel}
            selected={activeScenarios[scenario.id]}
            onPress={() => toggleScenario(scenario.id)}
            color={scenario.color}
          />
        ))}
      </View>

      {/* Chart */}
      <Card style={styles.chartCard}>
        <Text style={styles.chartTitle}>Evolução Patrimonial (20 anos)</Text>
        {chartData.length > 0 && activeKeys.length > 0 ? (
          <LineChart
            data={chartData.filter(d => d.year <= 20)}
            width={SCREEN_WIDTH - Spacing.md * 2 - Spacing.md * 2 - 4}
            height={260}
            xKey="year"
            keys={activeKeys}
            colors={activeColors}
            axisOptions={{ font: null }}
          />
        ) : (
          <Text style={styles.placeholderText}>Selecione ao menos um cenário</Text>
        )}
        {/* Goal line reference */}
        <View style={styles.goalRef}>
          <View style={[styles.goalRefLine, { backgroundColor: Colors.danger }]} />
          <Text style={styles.goalRefLabel}>— Meta: R$ 3.000.000</Text>
        </View>
      </Card>

      {/* Scenario Summaries */}
      <Card style={styles.scenariosCard}>
        <SectionHeader title="Resumo por Cenário" />
        {SCENARIOS.map(scenario => {
          const proj = projections.find(p => p.scenarioId === scenario.id);
          const at10 = proj?.data.find(d => d.year === 10)?.value || 0;
          const at12 = proj?.data.find(d => d.year === 12)?.value || 0;

          return (
            <View key={scenario.id} style={styles.scenarioRow}>
              <View style={[styles.scenarioColorBar, { backgroundColor: scenario.color }]} />
              <View style={styles.scenarioInfo}>
                <Text style={[styles.scenarioName, { color: scenario.color }]}>
                  {scenario.label} ({(scenario.realRate * 100).toFixed(0)}% real)
                </Text>
                <View style={styles.scenarioValues}>
                  <Text style={styles.scenarioValue}>10a: {formatBRL(at10)}</Text>
                  <Text style={styles.scenarioValue}>12a: {formatBRL(at12)}</Text>
                  <Text style={[styles.scenarioGoal, { color: scenario.color }]}>
                    R$3M: {proj?.yearsToGoal ? `~${Math.ceil(proj.yearsToGoal)} anos` : '> 20 anos'}
                  </Text>
                </View>
              </View>
            </View>
          );
        })}
      </Card>

      {/* Milestones Table */}
      <Card style={styles.milestonesCard}>
        <SectionHeader title="Quando bate cada marco?" />
        <View style={styles.milestoneTable}>
          <View style={styles.milestoneHeader}>
            <Text style={[styles.milestoneCell, styles.milestoneHeaderText]}>Cenário</Text>
            {milestoneSummary.map(m => (
              <Text key={m.target} style={[styles.milestoneCell, styles.milestoneHeaderText]}>
                {m.label}
              </Text>
            ))}
          </View>
          {SCENARIOS.map(scenario => (
            <View key={scenario.id} style={styles.milestoneRow}>
              <Text style={[styles.milestoneCell, { color: scenario.color, fontWeight: '600' }]}>
                {scenario.shortLabel}
              </Text>
              {milestoneSummary.map(m => {
                const entry = m.byScenario.find(b => b.scenario.id === scenario.id);
                return (
                  <Text key={m.target} style={[styles.milestoneCell, { color: Colors.text }]}>
                    {entry?.years !== null && entry?.years !== undefined
                      ? `${Math.ceil(entry.years)}a`
                      : '—'}
                  </Text>
                );
              })}
            </View>
          ))}
        </View>
      </Card>

      {/* Leitura Executiva */}
      <Card style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>📋 Leitura Executiva</Text>
        <Text style={styles.summaryText}>
          Com aportes de {formatBRLFull(monthly * 12 + annual + extra)}/ano:
          {'\n\n'}• Cenário conservador (2%): R$3M em ~13 anos
          {'\n'}• Cenário base (4%): R$3M em ~12 anos
          {'\n'}• Cenário arrojado (6%): R$3M em ~11 anos
          {'\n'}• Cenário muito forte (8%): R$3M em ~10 anos
          {'\n\n'}Em 6 anos: entre R$1,34M e R$1,56M
          {'\n'}Em 10 anos: entre R$2,32M e R$3,08M
        </Text>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  header: { gap: 4, marginBottom: Spacing.xs },
  headerTitle: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  headerSubtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  inputCard: { gap: Spacing.sm },
  inputsRow: { flexDirection: 'row', gap: Spacing.sm },
  inputGroup: { flex: 1, gap: 4 },
  inputLabel: { color: Colors.textMuted, fontSize: FontSize.xs, fontWeight: '500' },
  input: {
    backgroundColor: Colors.bgInput,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    color: Colors.text,
    fontSize: FontSize.sm,
    padding: Spacing.sm,
  },
  inputTotal: {
    color: Colors.accent,
    fontSize: FontSize.sm,
    fontWeight: '700',
    textAlign: 'right',
  },
  scenarioToggles: { flexDirection: 'row', gap: Spacing.sm, flexWrap: 'wrap' },
  chartCard: { gap: Spacing.sm },
  chartTitle: { color: Colors.text, fontSize: FontSize.md, fontWeight: '700' },
  placeholderText: { color: Colors.textMuted, textAlign: 'center', padding: Spacing.lg },
  goalRef: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginTop: 4 },
  goalRefLine: { width: 24, height: 2 },
  goalRefLabel: { color: Colors.textMuted, fontSize: FontSize.xs },
  scenariosCard: { gap: Spacing.md },
  scenarioRow: { flexDirection: 'row', gap: Spacing.sm, alignItems: 'flex-start' },
  scenarioColorBar: { width: 3, borderRadius: 2, marginTop: 4, alignSelf: 'stretch', minHeight: 40 },
  scenarioInfo: { flex: 1, gap: 4 },
  scenarioName: { fontSize: FontSize.sm, fontWeight: '700' },
  scenarioValues: { flexDirection: 'row', gap: Spacing.md, flexWrap: 'wrap' },
  scenarioValue: { color: Colors.textSecondary, fontSize: FontSize.xs },
  scenarioGoal: { fontSize: FontSize.xs, fontWeight: '700' },
  milestonesCard: { gap: Spacing.sm },
  milestoneTable: { gap: 0 },
  milestoneHeader: {
    flexDirection: 'row',
    backgroundColor: Colors.bgCardHover,
    borderRadius: 8,
    marginBottom: 2,
    padding: Spacing.xs,
  },
  milestoneHeaderText: {
    color: Colors.textMuted,
    fontWeight: '700',
    fontSize: FontSize.xs,
    textTransform: 'uppercase',
  },
  milestoneRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    padding: Spacing.xs,
  },
  milestoneCell: {
    flex: 1,
    fontSize: FontSize.sm,
    textAlign: 'center',
    color: Colors.text,
  },
  summaryCard: { borderColor: Colors.accentDark, gap: Spacing.sm },
  summaryTitle: { color: Colors.accentLight, fontSize: FontSize.md, fontWeight: '700' },
  summaryText: { color: Colors.text, fontSize: FontSize.sm, lineHeight: 22 },
});
