import React, { useCallback, useEffect } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, RefreshControl,
} from 'react-native';
import { router } from 'expo-router';
import { BarChart } from 'victory-native';
import { usePortfolioStore } from '../../src/store/usePortfolioStore';
import { summarizeByCategory, EXPENSE_CATEGORIES } from '../../src/utils/categorizer';
import { formatBRL, formatBRLFull } from '../../src/utils/calculations';
import { Card, SectionHeader, StatCard, EmptyState, LoadingSpinner } from '../../src/components/shared';
import { Colors, Spacing, FontSize, Radius } from '../../src/constants/colors';
import { SUPPORTED_INSTITUTIONS } from '../../src/services/pluggy';
import { Dimensions } from 'react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function FinancesScreen() {
  const store = usePortfolioStore();
  const {
    bankAccounts,
    transactions,
    financialSummary,
    realInvestments,
    isLoadingOpenFinance,
    openFinanceError,
    pluggyItemIds,
    monthlyContribution,
    annualContribution,
  } = store;

  const categories = summarizeByCategory(
    transactions.map(tx => ({
      description: tx.description,
      amount: tx.amount,
      type: tx.type,
    }))
  );

  const onRefresh = useCallback(() => {
    store.refreshOpenFinance();
  }, []);

  useEffect(() => {
    if (pluggyItemIds.length > 0) {
      store.refreshOpenFinance();
    }
  }, [pluggyItemIds.length]);

  const isOnTrack = financialSummary
    ? financialSummary.monthBalance >= monthlyContribution
    : false;

  const barData = categories.slice(0, 6).map(c => ({
    x: c.info.label.substring(0, 8),
    y: c.total,
    fill: c.info.color,
  }));

  if (isLoadingOpenFinance) {
    return <LoadingSpinner text="Sincronizando dados bancários..." />;
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={isLoadingOpenFinance}
          onRefresh={onRefresh}
          tintColor={Colors.accent}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Finanças</Text>
        <Text style={styles.headerSubtitle}>Open Finance — seus dados reais</Text>
      </View>

      {/* Connect Bank CTA */}
      {pluggyItemIds.length === 0 ? (
        <EmptyState
          icon="🏦"
          title="Conecte sua conta bancária"
          description="Veja todos os seus gastos, receitas e investimentos reais em um lugar. Suportamos íon, Nubank, BTG, XP, Bradesco e +60 instituições."
          action={{ label: 'Conectar banco agora', onPress: () => router.push('/modal/connect-bank') }}
        />
      ) : (
        <>
          {/* Connected Accounts */}
          <Card>
            <SectionHeader
              title="Contas Conectadas"
              action={{ label: '+ Adicionar', onPress: () => router.push('/modal/connect-bank') }}
            />
            {bankAccounts.length === 0 ? (
              <Text style={styles.emptyText}>Nenhuma conta carregada</Text>
            ) : (
              <View style={styles.accountsList}>
                {bankAccounts.map(acc => (
                  <View key={acc.id} style={styles.accountItem}>
                    <View style={styles.accountInfo}>
                      <Text style={styles.accountName}>{acc.name}</Text>
                      <Text style={styles.accountType}>{acc.type} • {acc.institution || 'Banco'}</Text>
                    </View>
                    <Text style={styles.accountBalance}>{formatBRL(acc.balance)}</Text>
                  </View>
                ))}
              </View>
            )}
          </Card>

          {/* Error */}
          {openFinanceError && (
            <Card style={styles.errorCard}>
              <Text style={styles.errorText}>⚠️ {openFinanceError}</Text>
            </Card>
          )}

          {/* Monthly Summary */}
          {financialSummary && (
            <>
              <View style={styles.statsGrid}>
                <StatCard
                  label="Receita do mês"
                  value={formatBRL(financialSummary.monthIncome)}
                  icon="📈"
                  trend="up"
                  style={styles.statHalf}
                />
                <StatCard
                  label="Gastos do mês"
                  value={formatBRL(financialSummary.monthExpenses)}
                  icon="📉"
                  trend="down"
                  style={styles.statHalf}
                />
                <StatCard
                  label="Saldo líquido"
                  value={formatBRL(financialSummary.monthBalance)}
                  icon="⚖️"
                  trend={financialSummary.monthBalance >= 0 ? 'up' : 'down'}
                  color={financialSummary.monthBalance >= 0 ? Colors.success : Colors.danger}
                  style={styles.statHalf}
                />
                <StatCard
                  label="Sobra p/ investir"
                  value={formatBRL(financialSummary.availableToInvest)}
                  icon="💰"
                  color={Colors.accent}
                  style={styles.statHalf}
                />
              </View>

              {/* On Track Indicator */}
              <Card style={[styles.onTrackCard, isOnTrack ? styles.onTrackSuccess : styles.onTrackWarning]}>
                <Text style={styles.onTrackIcon}>{isOnTrack ? '✅' : '⚠️'}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.onTrackTitle}>
                    {isOnTrack ? 'No trilho do plano!' : 'Abaixo do aporte mensal'}
                  </Text>
                  <Text style={styles.onTrackDesc}>
                    {isOnTrack
                      ? `Sobra R$ ${formatBRL(financialSummary.availableToInvest - monthlyContribution)} acima do aporte mensal de R$ ${formatBRL(monthlyContribution)}`
                      : `Aporte mensal: R$ ${formatBRL(monthlyContribution)}. Saldo disponível: R$ ${formatBRL(financialSummary.availableToInvest)}`
                    }
                  </Text>
                </View>
              </Card>
            </>
          )}

          {/* Expense Chart */}
          {categories.length > 0 && (
            <Card>
              <SectionHeader title="Gastos por Categoria" />
              {barData.length > 0 && (
                <BarChart
                  data={barData}
                  width={SCREEN_WIDTH - Spacing.md * 2 - Spacing.md * 2 - 4}
                  height={200}
                  xKey="x"
                  keys={['y'] as const}
                  colors={barData.map(d => d.fill)}
                  axisOptions={{ font: null }}
                />
              )}
              <View style={styles.categoryList}>
                {categories.slice(0, 8).map(cat => (
                  <View key={cat.category} style={styles.categoryItem}>
                    <Text style={styles.categoryIcon}>{cat.info.icon}</Text>
                    <View style={styles.categoryInfo}>
                      <View style={styles.categoryLabelRow}>
                        <Text style={styles.categoryLabel}>{cat.info.label}</Text>
                        {cat.info.dedutiveIR && (
                          <View style={styles.irBadge}>
                            <Text style={styles.irBadgeText}>IR dedutível</Text>
                          </View>
                        )}
                      </View>
                      <View style={styles.categoryBar}>
                        <View
                          style={[
                            styles.categoryBarFill,
                            { width: `${cat.percentage}%` as any, backgroundColor: cat.info.color },
                          ]}
                        />
                      </View>
                    </View>
                    <Text style={styles.categoryAmount}>{formatBRL(cat.total)}</Text>
                  </View>
                ))}
              </View>
            </Card>
          )}

          {/* Recent Transactions */}
          <Card>
            <SectionHeader title="Últimas Transações" />
            {transactions.length === 0 ? (
              <Text style={styles.emptyText}>Nenhuma transação encontrada</Text>
            ) : (
              <View style={styles.transactionList}>
                {transactions.slice(0, 20).map(tx => (
                  <View key={tx.id} style={styles.transactionItem}>
                    <View style={styles.txInfo}>
                      <Text style={styles.txDescription} numberOfLines={1}>{tx.description}</Text>
                      <Text style={styles.txDate}>{new Date(tx.date).toLocaleDateString('pt-BR')}</Text>
                    </View>
                    <Text style={[
                      styles.txAmount,
                      { color: tx.type === 'CREDIT' ? Colors.success : Colors.text }
                    ]}>
                      {tx.type === 'CREDIT' ? '+' : '-'}{formatBRL(tx.amount)}
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </Card>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  header: { gap: 4 },
  headerTitle: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  headerSubtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  emptyText: { color: Colors.textMuted, textAlign: 'center', padding: Spacing.md },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  statHalf: { width: (SCREEN_WIDTH - Spacing.md * 2 - Spacing.sm) / 2 - 1 },
  accountsList: { gap: Spacing.sm },
  accountItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  accountInfo: { flex: 1 },
  accountName: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '600' },
  accountType: { color: Colors.textMuted, fontSize: FontSize.xs },
  accountBalance: { color: Colors.accent, fontSize: FontSize.sm, fontWeight: '700' },
  errorCard: { borderColor: Colors.danger },
  errorText: { color: Colors.danger, fontSize: FontSize.sm },
  onTrackCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    borderWidth: 1,
  },
  onTrackSuccess: { borderColor: Colors.success, backgroundColor: Colors.successBg },
  onTrackWarning: { borderColor: Colors.warning, backgroundColor: Colors.warningBg },
  onTrackIcon: { fontSize: 24 },
  onTrackTitle: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '700' },
  onTrackDesc: { color: Colors.textSecondary, fontSize: FontSize.xs, marginTop: 2 },
  categoryList: { gap: Spacing.sm, marginTop: Spacing.sm },
  categoryItem: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  categoryIcon: { fontSize: 20, width: 28 },
  categoryInfo: { flex: 1, gap: 4 },
  categoryLabelRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  categoryLabel: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '600' },
  irBadge: {
    backgroundColor: Colors.accentBg,
    borderRadius: Radius.full,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  irBadgeText: { color: Colors.accentLight, fontSize: 9, fontWeight: '700' },
  categoryBar: {
    height: 6,
    backgroundColor: Colors.bgCardHover,
    borderRadius: 3,
    overflow: 'hidden',
  },
  categoryBarFill: { height: 6, borderRadius: 3 },
  categoryAmount: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '700', minWidth: 70, textAlign: 'right' },
  transactionList: { gap: Spacing.xs },
  transactionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  txInfo: { flex: 1, gap: 2 },
  txDescription: { color: Colors.text, fontSize: FontSize.sm },
  txDate: { color: Colors.textMuted, fontSize: FontSize.xs },
  txAmount: { fontSize: FontSize.sm, fontWeight: '700', minWidth: 80, textAlign: 'right' },
});
