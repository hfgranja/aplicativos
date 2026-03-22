import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TextInput, TouchableOpacity, Alert,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { usePortfolioStore } from '../../src/store/usePortfolioStore';
import { simulateBuy } from '../../src/services/tradingSimulator';
import { checkStockSaleIRRule } from '../../src/services/tradingSimulator';
import { INVESTMENTS, InvestmentCategory } from '../../src/constants/investments';
import { formatBRLFull } from '../../src/utils/calculations';
import { Card, LoadingSpinner } from '../../src/components/shared';
import { Colors, Spacing, Radius, FontSize } from '../../src/constants/colors';

export default function TradeModal() {
  const params = useLocalSearchParams<{ ticker?: string; name?: string; price?: string }>();
  const store = usePortfolioStore();

  const [ticker, setTicker] = useState(params.ticker || '');
  const [investmentName, setInvestmentName] = useState(params.name || '');
  const [amount, setAmount] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<InvestmentCategory>('variable');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const tradeableInvestments = INVESTMENTS.filter(inv => inv.ticker);

  const monthlyStockSales = store.paperPositions
    .filter(p => p.type === 'stock' || p.type === 'etf')
    .reduce((sum, p) => sum + p.currentPrice * p.quantity, 0);

  const irCheck = checkStockSaleIRRule(monthlyStockSales);

  const handleTrade = async () => {
    if (!ticker.trim()) {
      setError('Informe o ticker do ativo');
      return;
    }
    const amountNum = parseFloat(amount.replace(',', '.'));
    if (!amountNum || amountNum <= 0) {
      setError('Informe um valor válido');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const position = await simulateBuy(
        ticker.toUpperCase(),
        investmentName || ticker.toUpperCase(),
        amountNum,
        selectedCategory,
        selectedCategory === 'variable' ? 'etf' : selectedCategory === 'ipcaPlus' ? 'tesouro' : 'cdb',
      );

      store.addPaperPosition(position);
      Alert.alert(
        '✅ Posição Simulada',
        `Comprado: ${position.quantity} cotas de ${position.ticker}\nPreço: R$ ${position.avgPrice.toFixed(2)}\nTotal: ${formatBRLFull(position.quantity * position.avgPrice)}`,
        [{ text: 'OK', onPress: () => router.back() }]
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao simular trade');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner text="Buscando cotação e simulando compra..." />;
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Simular Compra</Text>
      <Text style={styles.subtitle}>Paper trading com preços reais de mercado</Text>

      {/* Quick Select */}
      <Card>
        <Text style={styles.sectionLabel}>Ativos negociáveis (clique para preencher)</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.tickerChips}>
            {tradeableInvestments.map(inv => (
              <TouchableOpacity
                key={inv.id}
                style={[styles.chip, ticker === inv.ticker && styles.chipActive]}
                onPress={() => {
                  setTicker(inv.ticker || '');
                  setInvestmentName(inv.name);
                  setSelectedCategory(inv.category);
                }}
              >
                <Text style={[styles.chipText, ticker === inv.ticker && styles.chipTextActive]}>
                  {inv.ticker}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </Card>

      {/* Trade Form */}
      <Card style={styles.formCard}>
        <View style={styles.formGroup}>
          <Text style={styles.formLabel}>Ticker *</Text>
          <TextInput
            style={styles.formInput}
            value={ticker}
            onChangeText={v => setTicker(v.toUpperCase())}
            placeholder="Ex: BOVA11, PETR4"
            placeholderTextColor={Colors.textMuted}
            autoCapitalize="characters"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.formLabel}>Nome (opcional)</Text>
          <TextInput
            style={styles.formInput}
            value={investmentName}
            onChangeText={setInvestmentName}
            placeholder="Ex: iShares Ibovespa ETF"
            placeholderTextColor={Colors.textMuted}
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.formLabel}>Valor a investir (R$) *</Text>
          <TextInput
            style={styles.formInput}
            value={amount}
            onChangeText={setAmount}
            placeholder="Ex: 5000"
            placeholderTextColor={Colors.textMuted}
            keyboardType="decimal-pad"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.formLabel}>Categoria</Text>
          <View style={styles.categoryBtns}>
            {([
              { id: 'ipcaPlus', label: 'IPCA+', color: Colors.ipcaPlus },
              { id: 'posFixed', label: 'Pós-fixado', color: Colors.posFixed },
              { id: 'variable', label: 'R. Variável', color: Colors.growth },
            ] as const).map(cat => (
              <TouchableOpacity
                key={cat.id}
                style={[
                  styles.categoryBtn,
                  selectedCategory === cat.id && { backgroundColor: cat.color, borderColor: cat.color }
                ]}
                onPress={() => setSelectedCategory(cat.id)}
              >
                <Text style={[
                  styles.categoryBtnText,
                  selectedCategory === cat.id ? { color: '#fff' } : { color: Colors.textSecondary }
                ]}>
                  {cat.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>⚠️ {error}</Text>
          </View>
        ) : null}

        <TouchableOpacity style={styles.submitBtn} onPress={handleTrade}>
          <Text style={styles.submitBtnText}>📊 Simular Compra</Text>
        </TouchableOpacity>
      </Card>

      {/* IR Warning */}
      {(selectedCategory === 'variable') && (
        <Card style={[
          styles.irCard,
          irCheck.warningLevel === 'taxable' ? styles.irCardDanger :
          irCheck.warningLevel === 'warning' ? styles.irCardWarning : styles.irCardSafe
        ]}>
          <Text style={styles.irTitle}>🧾 IR — Isenção de Ações</Text>
          <Text style={styles.irText}>{irCheck.message}</Text>
        </Card>
      )}

      <Text style={styles.disclaimer}>
        ⚠️ Paper trading — simulação educacional com preços reais. Não executa ordens reais. Consulte um profissional antes de investir.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  title: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  subtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  sectionLabel: { color: Colors.textSecondary, fontSize: FontSize.xs, marginBottom: Spacing.sm },
  tickerChips: { flexDirection: 'row', gap: Spacing.sm },
  chip: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs + 2,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: 'transparent',
  },
  chipActive: { backgroundColor: Colors.accent, borderColor: Colors.accent },
  chipText: { color: Colors.textSecondary, fontSize: FontSize.sm, fontWeight: '700' },
  chipTextActive: { color: '#fff' },
  formCard: { gap: Spacing.md },
  formGroup: { gap: 6 },
  formLabel: { color: Colors.textSecondary, fontSize: FontSize.sm, fontWeight: '600' },
  formInput: {
    backgroundColor: Colors.bgInput,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    color: Colors.text,
    fontSize: FontSize.md,
    padding: Spacing.md,
  },
  categoryBtns: { flexDirection: 'row', gap: Spacing.sm },
  categoryBtn: {
    flex: 1,
    paddingVertical: Spacing.sm,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  categoryBtnText: { fontSize: FontSize.sm, fontWeight: '600' },
  errorBox: {
    backgroundColor: Colors.dangerBg,
    borderRadius: Radius.sm,
    padding: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.danger,
  },
  errorText: { color: Colors.danger, fontSize: FontSize.sm },
  submitBtn: {
    backgroundColor: Colors.accent,
    borderRadius: Radius.md,
    padding: Spacing.md,
    alignItems: 'center',
  },
  submitBtnText: { color: '#fff', fontSize: FontSize.md, fontWeight: '800' },
  irCard: { borderWidth: 1, gap: Spacing.sm },
  irCardSafe: { borderColor: Colors.success, backgroundColor: Colors.successBg },
  irCardWarning: { borderColor: Colors.warning, backgroundColor: Colors.warningBg },
  irCardDanger: { borderColor: Colors.danger, backgroundColor: Colors.dangerBg },
  irTitle: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '700' },
  irText: { color: Colors.text, fontSize: FontSize.sm, lineHeight: 20 },
  disclaimer: { color: Colors.textMuted, fontSize: FontSize.xs, textAlign: 'center', lineHeight: 18 },
});
