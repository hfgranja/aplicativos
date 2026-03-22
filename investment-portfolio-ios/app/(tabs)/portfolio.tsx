import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Slider,
} from 'react-native';
import { router } from 'expo-router';
import { PieChart } from 'victory-native';
import { usePortfolioStore } from '../../src/store/usePortfolioStore';
import { calculatePortfolioPnL, getPositionPnL } from '../../src/services/tradingSimulator';
import { formatBRL, formatBRLFull } from '../../src/utils/calculations';
import { Card, SectionHeader, StatCard, EmptyState, RiskBadge } from '../../src/components/shared';
import { Colors, Spacing, Radius, FontSize } from '../../src/constants/colors';

export default function PortfolioScreen() {
  const store = usePortfolioStore();
  const { allocation, paperPositions, realInvestments, isLoadingOpenFinance } = store;

  const [ipcaVal, setIpcaVal] = useState(allocation.ipcaPlus);
  const [posFixedVal, setPosFixedVal] = useState(allocation.posFixed);
  const [growthVal, setGrowthVal] = useState(allocation.growth);

  const total = ipcaVal + posFixedVal + growthVal;
  const isValid = total === 100;

  const applyAllocation = () => {
    const sum = ipcaVal + posFixedVal + growthVal;
    if (sum > 0) {
      store.setAllocation({ ipcaPlus: ipcaVal, posFixed: posFixedVal, growth: growthVal });
    }
  };

  const pnlSummary = calculatePortfolioPnL(paperPositions);
  const realInvestmentsTotal = realInvestments.reduce((s, i) => s + i.balance, 0);
  const paperTotal = pnlSummary.currentValue;
  const totalPortfolio = realInvestmentsTotal + paperTotal;

  // Pie chart data
  const pieData = [
    { x: 'IPCA+', y: allocation.ipcaPlus, color: Colors.ipcaPlus },
    { x: 'Pós-fixado', y: allocation.posFixed, color: Colors.posFixed },
    { x: 'Crescimento', y: allocation.growth, color: Colors.growth },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Carteira</Text>
        <Text style={styles.headerSubtitle}>
          Patrimônio total: {formatBRL(totalPortfolio)}
        </Text>
      </View>

      {/* Allocation Pie + Sliders */}
      <Card style={styles.allocationCard}>
        <SectionHeader title="Alocação Alvo" />
        <View style={styles.pieContainer}>
          <PieChart
            data={pieData}
            width={200}
            height={200}
            innerRadius={55}
            colorScale={pieData.map(d => d.color)}
          />
          {/* Center label */}
          <View style={styles.pieCenter}>
            <Text style={styles.pieCenterValue}>{allocation.ipcaPlus}%</Text>
            <Text style={styles.pieCenterLabel}>IPCA+</Text>
          </View>
        </View>

        {/* Legend */}
        <View style={styles.pieLegend}>
          {[
            { label: 'IPCA+', pct: allocation.ipcaPlus, color: Colors.ipcaPlus },
            { label: 'Pós-fixado', pct: allocation.posFixed, color: Colors.posFixed },
            { label: 'Crescimento', pct: allocation.growth, color: Colors.growth },
          ].map(item => (
            <View key={item.label} style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: item.color }]} />
              <Text style={styles.legendLabel}>{item.label}</Text>
              <Text style={[styles.legendPct, { color: item.color }]}>{item.pct}%</Text>
            </View>
          ))}
        </View>

        {/* Sliders */}
        <View style={styles.slidersSection}>
          <Text style={styles.slidersTitle}>Ajustar Alocação</Text>

          {[
            { label: 'IPCA+ (recomendado: 50-60%)', value: ipcaVal, setValue: setIpcaVal, color: Colors.ipcaPlus },
            { label: 'Pós-fixado (recomendado: 20-30%)', value: posFixedVal, setValue: setPosFixedVal, color: Colors.posFixed },
            { label: 'Crescimento (recomendado: 15-25%)', value: growthVal, setValue: setGrowthVal, color: Colors.growth },
          ].map(item => (
            <View key={item.label} style={styles.sliderGroup}>
              <View style={styles.sliderLabelRow}>
                <Text style={styles.sliderLabel}>{item.label}</Text>
                <Text style={[styles.sliderValue, { color: item.color }]}>{item.value}%</Text>
              </View>
              <Slider
                style={styles.slider}
                minimumValue={0}
                maximumValue={100}
                value={item.value}
                step={1}
                minimumTrackTintColor={item.color}
                maximumTrackTintColor={Colors.bgCardHover}
                thumbTintColor={item.color}
                onValueChange={item.setValue}
                onSlidingComplete={applyAllocation}
              />
            </View>
          ))}

          <View style={styles.sliderTotal}>
            <Text style={styles.sliderTotalLabel}>Total</Text>
            <Text style={[styles.sliderTotalValue, isValid ? { color: Colors.success } : { color: Colors.danger }]}>
              {total}% {!isValid && '⚠️ deve ser 100%'}
            </Text>
          </View>
        </View>
      </Card>

      {/* Real Investments (Open Finance) */}
      <Card>
        <SectionHeader
          title="Investimentos Reais"
          subtitle="Via Open Finance"
          action={{ label: 'Conectar conta →', onPress: () => router.push('/modal/connect-bank') }}
        />
        {isLoadingOpenFinance ? (
          <Text style={styles.loadingText}>Carregando...</Text>
        ) : realInvestments.length === 0 ? (
          <EmptyState
            icon="🏦"
            title="Nenhuma conta conectada"
            description="Conecte seu íon, BTG, XP ou Nubank para ver seus investimentos reais aqui."
            action={{ label: 'Conectar banco', onPress: () => router.push('/modal/connect-bank') }}
          />
        ) : (
          <View style={styles.investmentsList}>
            {realInvestments.map(inv => (
              <View key={inv.id} style={styles.investmentItem}>
                <View style={styles.investmentInfo}>
                  <Text style={styles.investmentName}>{inv.name}</Text>
                  <Text style={styles.investmentType}>{inv.type.replace('_', ' ')}</Text>
                </View>
                <Text style={styles.investmentValue}>{formatBRL(inv.balance)}</Text>
              </View>
            ))}
            <View style={styles.investmentTotal}>
              <Text style={styles.investmentTotalLabel}>Total</Text>
              <Text style={styles.investmentTotalValue}>{formatBRLFull(realInvestmentsTotal)}</Text>
            </View>
          </View>
        )}
      </Card>

      {/* Paper Trading Positions */}
      <Card>
        <SectionHeader
          title="Paper Trading"
          subtitle="Simulação com preços reais"
          action={{ label: '+ Nova posição', onPress: () => router.push('/modal/trade') }}
        />
        {paperPositions.length === 0 ? (
          <EmptyState
            icon="📊"
            title="Nenhuma posição simulada"
            description="Simule compras com preços reais para planejar sua carteira."
            action={{ label: 'Simular trade', onPress: () => router.push('/modal/trade') }}
          />
        ) : (
          <View style={styles.positionsList}>
            {/* P&L Summary */}
            <View style={styles.pnlSummary}>
              <StatCard
                label="Investido"
                value={formatBRL(pnlSummary.totalInvested)}
                style={{ flex: 1 }}
              />
              <StatCard
                label="Atual"
                value={formatBRL(pnlSummary.currentValue)}
                style={{ flex: 1 }}
              />
              <StatCard
                label="P&L"
                value={formatBRL(Math.abs(pnlSummary.totalPnL))}
                subtitle={`${pnlSummary.totalPnLPct >= 0 ? '+' : ''}${pnlSummary.totalPnLPct.toFixed(2)}%`}
                trend={pnlSummary.totalPnL >= 0 ? 'up' : 'down'}
                color={pnlSummary.totalPnL >= 0 ? Colors.success : Colors.danger}
                style={{ flex: 1 }}
              />
            </View>

            {/* Individual Positions */}
            {paperPositions.map(pos => {
              const { pnl, pnlPct } = getPositionPnL(pos);
              return (
                <View key={pos.id} style={styles.positionItem}>
                  <View style={styles.positionHeader}>
                    <View>
                      <Text style={styles.positionTicker}>{pos.ticker}</Text>
                      <Text style={styles.positionName}>{pos.name}</Text>
                    </View>
                    <View style={styles.positionRight}>
                      <Text style={styles.positionValue}>
                        {formatBRL(pos.currentPrice * pos.quantity)}
                      </Text>
                      <Text style={[
                        styles.positionPnL,
                        { color: pnl >= 0 ? Colors.success : Colors.danger }
                      ]}>
                        {pnl >= 0 ? '+' : ''}{formatBRL(pnl)} ({pnlPct.toFixed(2)}%)
                      </Text>
                    </View>
                  </View>
                  <View style={styles.positionDetails}>
                    <Text style={styles.positionDetail}>{pos.quantity} cotas × R$ {pos.currentPrice.toFixed(2)}</Text>
                    <Text style={styles.positionDetail}>Compra: R$ {pos.avgPrice.toFixed(2)}</Text>
                    <TouchableOpacity
                      onPress={() => store.removePaperPosition(pos.id)}
                      style={styles.removeBtn}
                    >
                      <Text style={styles.removeBtnText}>Remover</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  header: { gap: 4 },
  headerTitle: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  headerSubtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  allocationCard: { gap: Spacing.md },
  pieContainer: { alignItems: 'center', position: 'relative' },
  pieCenter: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -35 }, { translateY: -25 }],
    alignItems: 'center',
  },
  pieCenterValue: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  pieCenterLabel: { color: Colors.textMuted, fontSize: FontSize.xs },
  pieLegend: { flexDirection: 'row', justifyContent: 'space-around' },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendLabel: { color: Colors.textSecondary, fontSize: FontSize.sm },
  legendPct: { fontSize: FontSize.sm, fontWeight: '700' },
  slidersSection: { gap: Spacing.md, borderTopWidth: 1, borderTopColor: Colors.border, paddingTop: Spacing.md },
  slidersTitle: { color: Colors.textSecondary, fontSize: FontSize.sm, fontWeight: '600' },
  sliderGroup: { gap: 4 },
  sliderLabelRow: { flexDirection: 'row', justifyContent: 'space-between' },
  sliderLabel: { color: Colors.textSecondary, fontSize: FontSize.xs },
  sliderValue: { fontSize: FontSize.sm, fontWeight: '700' },
  slider: { width: '100%' },
  sliderTotal: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: Spacing.sm,
    backgroundColor: Colors.bgCardHover,
    borderRadius: 8,
  },
  sliderTotalLabel: { color: Colors.text, fontWeight: '700' },
  sliderTotalValue: { fontWeight: '700' },
  loadingText: { color: Colors.textMuted, textAlign: 'center', padding: Spacing.md },
  investmentsList: { gap: Spacing.sm },
  investmentItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  investmentInfo: { flex: 1 },
  investmentName: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '600' },
  investmentType: { color: Colors.textMuted, fontSize: FontSize.xs },
  investmentValue: { color: Colors.accent, fontSize: FontSize.sm, fontWeight: '700' },
  investmentTotal: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: Spacing.sm,
  },
  investmentTotalLabel: { color: Colors.textSecondary, fontWeight: '700' },
  investmentTotalValue: { color: Colors.text, fontWeight: '800' },
  positionsList: { gap: Spacing.md },
  pnlSummary: { flexDirection: 'row', gap: Spacing.sm },
  positionItem: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    padding: Spacing.sm,
    gap: Spacing.sm,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  positionTicker: { color: Colors.text, fontSize: FontSize.md, fontWeight: '800' },
  positionName: { color: Colors.textMuted, fontSize: FontSize.xs },
  positionRight: { alignItems: 'flex-end' },
  positionValue: { color: Colors.text, fontSize: FontSize.md, fontWeight: '700' },
  positionPnL: { fontSize: FontSize.xs, fontWeight: '600' },
  positionDetails: { flexDirection: 'row', gap: Spacing.md, flexWrap: 'wrap', alignItems: 'center' },
  positionDetail: { color: Colors.textMuted, fontSize: FontSize.xs },
  removeBtn: { marginLeft: 'auto' as any },
  removeBtnText: { color: Colors.danger, fontSize: FontSize.xs, fontWeight: '600' },
});
