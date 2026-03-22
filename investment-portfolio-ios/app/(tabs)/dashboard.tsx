import React, { useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, RefreshControl, StyleSheet,
  TouchableOpacity, Dimensions,
} from 'react-native';
import { router } from 'expo-router';
import { LineChart, CartesianChart, Line } from 'victory-native';
import { usePortfolioStore, selectTotalNetWorth } from '../../src/store/usePortfolioStore';
import { getAllScenarioProjections, formatBRL, goalProgress } from '../../src/utils/calculations';
import { Card, StatCard, ProgressBar, SectionHeader } from '../../src/components/shared';
import { Colors, Spacing, Radius, FontSize } from '../../src/constants/colors';
import { SCENARIOS } from '../../src/constants/scenarios';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function DashboardScreen() {
  const store = usePortfolioStore();
  const totalValue = selectTotalNetWorth(store);
  const progress = goalProgress(totalValue, store.goal);

  const { monthlyContribution, annualContribution, extraAnnualContribution, goal, marketIndices, aiSuggestions, marketAlerts } = store;

  const projections = getAllScenarioProjections({
    initialValue: totalValue,
    monthlyContribution,
    annualLumpSum: annualContribution,
    extraAnnualContribution,
    years: 15,
  });

  const baseProjection = projections.find(p => p.scenarioId === 'base');
  const yearsToGoalBase = baseProjection?.yearsToGoal;

  const onRefresh = useCallback(async () => {
    await Promise.all([
      store.refreshMarketData(),
      store.refreshOpenFinance(),
    ]);
  }, []);

  useEffect(() => {
    store.refreshMarketData();
  }, []);

  // Chart data for mini scenario chart
  const chartData = projections[0]?.data.map((snap, i) => ({
    year: snap.year,
    conservative: projections[0].data[i]?.value || 0,
    base: projections[1].data[i]?.value || 0,
    aggressive: projections[2].data[i]?.value || 0,
    veryStrong: projections[3].data[i]?.value || 0,
  })) || [];

  const latestAISuggestion = aiSuggestions[0];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={store.isLoadingMarket}
          onRefresh={onRefresh}
          tintColor={Colors.accent}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Meu Portfólio</Text>
          <Text style={styles.headerSubtitle}>
            {store.lastMarketUpdate
              ? `Atualizado às ${store.lastMarketUpdate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
              : 'Toque para atualizar'}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.settingsBtn}
          onPress={() => router.push('/settings')}
        >
          <Text style={styles.settingsBtnText}>⚙️</Text>
        </TouchableOpacity>
      </View>

      {/* Goal Progress Card */}
      <Card style={styles.goalCard}>
        <Text style={styles.goalLabel}>META: {formatBRL(goal)}</Text>
        <View style={styles.goalValueRow}>
          <Text style={styles.goalValue}>{formatBRL(totalValue)}</Text>
          <Text style={styles.goalPct}>{progress.toFixed(1)}%</Text>
        </View>
        <ProgressBar
          progress={progress}
          color={Colors.accent}
          height={12}
          style={{ marginTop: Spacing.sm }}
        />
        <View style={styles.goalMilestones}>
          {[1000000, 2000000, 3000000].map(m => (
            <View key={m} style={styles.milestone}>
              <View style={[styles.milestoneDot, totalValue >= m ? styles.milestoneDotActive : {}]} />
              <Text style={[styles.milestoneLabel, totalValue >= m ? styles.milestoneLabelActive : {}]}>
                {formatBRL(m)}
              </Text>
            </View>
          ))}
        </View>
      </Card>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        <StatCard
          label="Patrimônio"
          value={formatBRL(totalValue)}
          icon="💼"
          style={styles.statCardHalf}
        />
        <StatCard
          label="Aporte Anual"
          value={formatBRL(monthlyContribution * 12 + annualContribution + extraAnnualContribution)}
          icon="💰"
          style={styles.statCardHalf}
        />
        <StatCard
          label="Anos p/ R$3M"
          value={yearsToGoalBase !== null && yearsToGoalBase !== undefined
            ? `~${Math.ceil(yearsToGoalBase)} anos`
            : '10-12 anos'}
          icon="⏱️"
          subtitle="Cenário base (4% real)"
          style={styles.statCardHalf}
        />
        <StatCard
          label="SELIC / CDI"
          value={marketIndices ? `${marketIndices.selic.toFixed(2)}%` : '—'}
          icon="📊"
          subtitle={marketIndices ? `IPCA: ${marketIndices.ipca.toFixed(2)}%` : ''}
          style={styles.statCardHalf}
        />
      </View>

      {/* Mini Projections Chart */}
      <Card style={styles.chartCard}>
        <SectionHeader
          title="Projeções (15 anos)"
          action={{ label: 'Ver detalhes →', onPress: () => router.push('/(tabs)/projections') }}
        />
        {chartData.length > 0 ? (
          <View style={styles.chartContainer}>
            <LineChart
              data={chartData}
              width={SCREEN_WIDTH - Spacing.md * 2 - Spacing.md * 2 - 2}
              height={180}
              xKey="year"
              keys={['conservative', 'base', 'aggressive', 'veryStrong'] as const}
              colors={SCENARIOS.map(s => s.color)}
              axisOptions={{ font: null }}
            />
            {/* Legend */}
            <View style={styles.legend}>
              {SCENARIOS.map(s => (
                <View key={s.id} style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: s.color }]} />
                  <Text style={styles.legendLabel}>{s.shortLabel}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : (
          <Text style={styles.placeholderText}>Carregando projeções...</Text>
        )}
      </Card>

      {/* Market Alerts */}
      {marketAlerts.length > 0 && (
        <Card style={styles.alertsCard}>
          <SectionHeader title="🔔 Alertas do Mercado" />
          {marketAlerts.map((alert, i) => (
            <View key={i} style={styles.alertItem}>
              <Text style={styles.alertDot}>•</Text>
              <Text style={styles.alertText}>{alert}</Text>
            </View>
          ))}
        </Card>
      )}

      {/* AI Insight */}
      {latestAISuggestion && (
        <Card style={styles.aiCard} onPress={() => router.push('/(tabs)/ai-advisor')}>
          <View style={styles.aiHeader}>
            <Text style={styles.aiIcon}>🤖</Text>
            <Text style={styles.aiTitle}>{latestAISuggestion.title}</Text>
          </View>
          <Text style={styles.aiContent} numberOfLines={4}>
            {latestAISuggestion.content}
          </Text>
          <Text style={styles.aiSeeMore}>Ver análise completa →</Text>
        </Card>
      )}

      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={styles.actionBtn}
          onPress={() => router.push('/modal/trade')}
        >
          <Text style={styles.actionBtnIcon}>📊</Text>
          <Text style={styles.actionBtnLabel}>Simular Trade</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionBtn}
          onPress={() => router.push('/modal/ir-advisor')}
        >
          <Text style={styles.actionBtnIcon}>🧾</Text>
          <Text style={styles.actionBtnLabel}>Imposto de Renda</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionBtn}
          onPress={() => router.push('/modal/strategy')}
        >
          <Text style={styles.actionBtnIcon}>🎯</Text>
          <Text style={styles.actionBtnLabel}>Estratégia</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  headerTitle: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  headerSubtitle: { color: Colors.textMuted, fontSize: FontSize.xs, marginTop: 2 },
  settingsBtn: { padding: Spacing.sm },
  settingsBtnText: { fontSize: 22 },
  goalCard: { gap: Spacing.sm },
  goalLabel: {
    color: Colors.textMuted,
    fontSize: FontSize.xs,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  goalValueRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
  },
  goalValue: { color: Colors.text, fontSize: FontSize.xxxl, fontWeight: '800' },
  goalPct: { color: Colors.accent, fontSize: FontSize.xl, fontWeight: '700' },
  goalMilestones: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: Spacing.sm,
  },
  milestone: { alignItems: 'center', gap: 4 },
  milestoneDot: {
    width: 8, height: 8, borderRadius: 4,
    backgroundColor: Colors.bgCardHover,
    borderWidth: 1, borderColor: Colors.border,
  },
  milestoneDotActive: { backgroundColor: Colors.accent, borderColor: Colors.accent },
  milestoneLabel: { color: Colors.textMuted, fontSize: FontSize.xs },
  milestoneLabelActive: { color: Colors.accent },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  statCardHalf: { width: (SCREEN_WIDTH - Spacing.md * 2 - Spacing.sm) / 2 - 1 },
  chartCard: { gap: Spacing.sm },
  chartContainer: { gap: Spacing.sm },
  legend: { flexDirection: 'row', justifyContent: 'center', gap: Spacing.md, flexWrap: 'wrap' },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendLabel: { color: Colors.textSecondary, fontSize: FontSize.xs },
  placeholderText: { color: Colors.textMuted, fontSize: FontSize.sm, textAlign: 'center', padding: Spacing.lg },
  alertsCard: { borderColor: Colors.warning, gap: Spacing.sm },
  alertItem: { flexDirection: 'row', gap: Spacing.sm },
  alertDot: { color: Colors.warning, fontSize: FontSize.md },
  alertText: { color: Colors.text, fontSize: FontSize.sm, flex: 1, lineHeight: 20 },
  aiCard: { borderColor: Colors.accentDark, gap: Spacing.sm },
  aiHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  aiIcon: { fontSize: 20 },
  aiTitle: { color: Colors.accentLight, fontSize: FontSize.md, fontWeight: '700' },
  aiContent: { color: Colors.text, fontSize: FontSize.sm, lineHeight: 22 },
  aiSeeMore: { color: Colors.accent, fontSize: FontSize.sm, fontWeight: '600', textAlign: 'right' },
  quickActions: { flexDirection: 'row', gap: Spacing.sm },
  actionBtn: {
    flex: 1,
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.md,
    alignItems: 'center',
    gap: Spacing.xs,
  },
  actionBtnIcon: { fontSize: 24 },
  actionBtnLabel: { color: Colors.textSecondary, fontSize: FontSize.xs, fontWeight: '600', textAlign: 'center' },
});
