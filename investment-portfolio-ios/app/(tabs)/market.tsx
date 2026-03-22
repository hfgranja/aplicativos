import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, RefreshControl, TextInput,
} from 'react-native';
import { router } from 'expo-router';
import { usePortfolioStore } from '../../src/store/usePortfolioStore';
import { formatBRL } from '../../src/utils/calculations';
import { Card, SectionHeader, RiskBadge, EmptyState, LoadingSpinner } from '../../src/components/shared';
import { Colors, Spacing, FontSize, Radius } from '../../src/constants/colors';
import { INVESTMENTS, INVESTMENT_CATEGORIES, InvestmentCategory } from '../../src/constants/investments';

const TABS: { id: InvestmentCategory | 'all'; label: string }[] = [
  { id: 'all', label: 'Todos' },
  { id: 'ipcaPlus', label: 'IPCA+' },
  { id: 'posFixed', label: 'Pós-fixado' },
  { id: 'prefixed', label: 'Prefixado' },
  { id: 'variable', label: 'R. Variável' },
  { id: 'pension', label: 'Previdência' },
];

export default function MarketScreen() {
  const store = usePortfolioStore();
  const { marketQuotes, tesouroBonds, marketIndices, isLoadingMarket, lastMarketUpdate } = store;

  const [activeTab, setActiveTab] = useState<InvestmentCategory | 'all'>('all');
  const [search, setSearch] = useState('');

  const onRefresh = useCallback(() => {
    store.refreshMarketData();
  }, []);

  const filteredInvestments = INVESTMENTS.filter(inv => {
    const matchesTab = activeTab === 'all' || inv.category === activeTab;
    const matchesSearch = search.length === 0 ||
      inv.name.toLowerCase().includes(search.toLowerCase()) ||
      (inv.ticker || '').toLowerCase().includes(search.toLowerCase());
    return matchesTab && matchesSearch;
  });

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={isLoadingMarket}
          onRefresh={onRefresh}
          tintColor={Colors.accent}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Mercado</Text>
        <Text style={styles.headerSubtitle}>
          {lastMarketUpdate
            ? `Atualizado: ${lastMarketUpdate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
            : 'Puxe para atualizar'}
        </Text>
      </View>

      {/* Market Indices */}
      {marketIndices && (
        <Card>
          <SectionHeader title="Indicadores" />
          <View style={styles.indicesGrid}>
            {[
              { label: 'SELIC', value: `${marketIndices.selic.toFixed(2)}%`, color: Colors.posFixed },
              { label: 'CDI', value: `${marketIndices.cdi.toFixed(2)}%`, color: Colors.posFixed },
              { label: 'IPCA 12m', value: `${marketIndices.ipca.toFixed(2)}%`, color: Colors.warning },
              { label: 'USD/BRL', value: `R$ ${marketIndices.usdBrl.toFixed(2)}`, color: Colors.textSecondary },
              { label: 'Ibovespa', value: `${(marketIndices.ibovespa / 1000).toFixed(1)}k`, color: marketIndices.ibovespaChange >= 0 ? Colors.success : Colors.danger },
              { label: 'Variação', value: `${marketIndices.ibovespaChange >= 0 ? '+' : ''}${marketIndices.ibovespaChange.toFixed(2)}%`, color: marketIndices.ibovespaChange >= 0 ? Colors.success : Colors.danger },
            ].map(ind => (
              <View key={ind.label} style={styles.indexItem}>
                <Text style={styles.indexLabel}>{ind.label}</Text>
                <Text style={[styles.indexValue, { color: ind.color }]}>{ind.value}</Text>
              </View>
            ))}
          </View>
        </Card>
      )}

      {/* Live Quotes from Brapi */}
      {Object.keys(marketQuotes).length > 0 && (
        <Card>
          <SectionHeader title="Cotações ao Vivo" subtitle="Brapi.dev" />
          <View style={styles.quotesList}>
            {Object.values(marketQuotes).map(quote => (
              <View key={quote.ticker} style={styles.quoteItem}>
                <View style={styles.quoteInfo}>
                  <Text style={styles.quoteTicker}>{quote.ticker}</Text>
                  <Text style={styles.quoteName} numberOfLines={1}>{quote.name}</Text>
                </View>
                <View style={styles.quoteRight}>
                  <Text style={styles.quotePrice}>R$ {quote.price.toFixed(2)}</Text>
                  <Text style={[
                    styles.quoteChange,
                    { color: quote.changePercent >= 0 ? Colors.success : Colors.danger }
                  ]}>
                    {quote.changePercent >= 0 ? '▲' : '▼'} {Math.abs(quote.changePercent).toFixed(2)}%
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.tradeBtn}
                  onPress={() => router.push({
                    pathname: '/modal/trade',
                    params: { ticker: quote.ticker, name: quote.name, price: quote.price },
                  })}
                >
                  <Text style={styles.tradeBtnText}>Simular</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        </Card>
      )}

      {/* Tesouro Direto */}
      {tesouroBonds.length > 0 && (
        <Card>
          <SectionHeader title="Tesouro Direto" subtitle="Dados oficiais B3/Tesouro" />
          <View style={styles.bondsList}>
            {tesouroBonds.map(bond => (
              <View key={bond.id} style={styles.bondItem}>
                <View style={styles.bondInfo}>
                  <Text style={styles.bondName}>{bond.name}</Text>
                  <Text style={styles.bondMeta}>
                    Venc: {bond.maturityDate ? new Date(bond.maturityDate).toLocaleDateString('pt-BR', { month: '2-digit', year: 'numeric' }) : '—'}
                    {' '}• Mín: {formatBRL(bond.minimumAmount)}
                  </Text>
                </View>
                <View style={styles.bondRight}>
                  <Text style={styles.bondRate}>
                    {bond.indexer === 'SELIC' ? 'SELIC' : bond.indexer === 'IPCA' ? 'IPCA+' : ''}
                    {bond.annualRate > 0 ? ` ${bond.annualRate.toFixed(2)}%` : ''}
                  </Text>
                  <Text style={styles.bondPrice}>R$ {bond.unitPrice.toFixed(2)}</Text>
                </View>
              </View>
            ))}
          </View>
        </Card>
      )}

      {/* Investment Catalog */}
      <Card>
        <SectionHeader title="Catálogo de Investimentos" />

        {/* Search */}
        <TextInput
          style={styles.searchInput}
          value={search}
          onChangeText={setSearch}
          placeholder="Buscar investimento..."
          placeholderTextColor={Colors.textMuted}
        />

        {/* Category Tabs */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabsScroll}>
          <View style={styles.tabs}>
            {TABS.map(tab => (
              <TouchableOpacity
                key={tab.id}
                style={[styles.tab, activeTab === tab.id && styles.tabActive]}
                onPress={() => setActiveTab(tab.id)}
              >
                <Text style={[styles.tabText, activeTab === tab.id && styles.tabTextActive]}>
                  {tab.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>

        {/* Investment Cards */}
        <View style={styles.investmentCards}>
          {filteredInvestments.length === 0 ? (
            <Text style={styles.emptyText}>Nenhum investimento encontrado</Text>
          ) : (
            filteredInvestments.map(inv => (
              <View key={inv.id} style={styles.investmentCard}>
                <View style={styles.investmentCardHeader}>
                  <View style={styles.investmentCardInfo}>
                    <Text style={styles.investmentCardName}>{inv.name}</Text>
                    {inv.ticker && (
                      <Text style={styles.investmentCardTicker}>{inv.ticker}</Text>
                    )}
                  </View>
                  <View style={styles.investmentCardBadges}>
                    <RiskBadge level={inv.riskLevel} />
                    {inv.isencaoIR && (
                      <View style={styles.isencaoBadge}>
                        <Text style={styles.isencaoText}>Isento IR</Text>
                      </View>
                    )}
                  </View>
                </View>

                <View style={styles.investmentCardMeta}>
                  <View style={styles.metaItem}>
                    <Text style={styles.metaLabel}>Retorno</Text>
                    <Text style={styles.metaValue}>{inv.typicalReturn}</Text>
                  </View>
                  <View style={styles.metaItem}>
                    <Text style={styles.metaLabel}>Liquidez</Text>
                    <Text style={styles.metaValue}>{inv.liquidity}</Text>
                  </View>
                  <View style={styles.metaItem}>
                    <Text style={styles.metaLabel}>Mínimo</Text>
                    <Text style={styles.metaValue}>{formatBRL(inv.minInvestment)}</Text>
                  </View>
                </View>

                <Text style={styles.investmentCardDesc} numberOfLines={2}>{inv.description}</Text>

                <View style={styles.whereToBuy}>
                  <Text style={styles.whereLabel}>Onde comprar: </Text>
                  <Text style={styles.whereValue}>{inv.where.join(', ')}</Text>
                </View>
              </View>
            ))
          )}
        </View>
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
  indicesGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  indexItem: {
    width: '30%',
    backgroundColor: Colors.bgCardHover,
    borderRadius: Radius.sm,
    padding: Spacing.sm,
    gap: 2,
  },
  indexLabel: { color: Colors.textMuted, fontSize: FontSize.xs, fontWeight: '500' },
  indexValue: { fontSize: FontSize.md, fontWeight: '700' },
  quotesList: { gap: Spacing.sm },
  quoteItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  quoteInfo: { flex: 1 },
  quoteTicker: { color: Colors.text, fontSize: FontSize.md, fontWeight: '800' },
  quoteName: { color: Colors.textMuted, fontSize: FontSize.xs },
  quoteRight: { alignItems: 'flex-end' },
  quotePrice: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '700' },
  quoteChange: { fontSize: FontSize.xs, fontWeight: '600' },
  tradeBtn: {
    backgroundColor: Colors.accentBg,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.accent,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
  },
  tradeBtnText: { color: Colors.accent, fontSize: FontSize.xs, fontWeight: '700' },
  bondsList: { gap: Spacing.sm },
  bondItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  bondInfo: { flex: 1 },
  bondName: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '600' },
  bondMeta: { color: Colors.textMuted, fontSize: FontSize.xs, marginTop: 2 },
  bondRight: { alignItems: 'flex-end' },
  bondRate: { color: Colors.ipcaPlus, fontSize: FontSize.sm, fontWeight: '700' },
  bondPrice: { color: Colors.textSecondary, fontSize: FontSize.xs },
  searchInput: {
    backgroundColor: Colors.bgInput,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    color: Colors.text,
    fontSize: FontSize.sm,
    padding: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  tabsScroll: { marginBottom: Spacing.sm },
  tabs: { flexDirection: 'row', gap: Spacing.xs },
  tab: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs + 2,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: 'transparent',
  },
  tabActive: { backgroundColor: Colors.accent, borderColor: Colors.accent },
  tabText: { color: Colors.textSecondary, fontSize: FontSize.xs, fontWeight: '600' },
  tabTextActive: { color: '#fff' },
  investmentCards: { gap: Spacing.md },
  investmentCard: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    padding: Spacing.md,
    gap: Spacing.sm,
    backgroundColor: Colors.bgCardHover,
  },
  investmentCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: Spacing.sm,
  },
  investmentCardInfo: { flex: 1 },
  investmentCardName: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '700' },
  investmentCardTicker: { color: Colors.accent, fontSize: FontSize.xs, fontWeight: '600' },
  investmentCardBadges: { gap: 4, alignItems: 'flex-end' },
  isencaoBadge: {
    backgroundColor: Colors.successBg,
    borderRadius: Radius.full,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderWidth: 1,
    borderColor: Colors.success,
  },
  isencaoText: { color: Colors.success, fontSize: 9, fontWeight: '700' },
  investmentCardMeta: { flexDirection: 'row', gap: Spacing.md },
  metaItem: { gap: 2 },
  metaLabel: { color: Colors.textMuted, fontSize: FontSize.xs },
  metaValue: { color: Colors.text, fontSize: FontSize.xs, fontWeight: '600' },
  investmentCardDesc: { color: Colors.textSecondary, fontSize: FontSize.xs, lineHeight: 18 },
  whereToBuy: { flexDirection: 'row', flexWrap: 'wrap' },
  whereLabel: { color: Colors.textMuted, fontSize: FontSize.xs },
  whereValue: { color: Colors.accentLight, fontSize: FontSize.xs, fontWeight: '600', flex: 1 },
  emptyText: { color: Colors.textMuted, textAlign: 'center', padding: Spacing.md },
});
