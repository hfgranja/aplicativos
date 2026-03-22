import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert,
} from 'react-native';
import { usePortfolioStore } from '../../src/store/usePortfolioStore';
import { analyzeIR } from '../../src/services/claudeAI';
import { detectDeductibleExpenses } from '../../src/utils/categorizer';
import { formatBRLFull } from '../../src/utils/calculations';
import { Card, SectionHeader, LoadingSpinner } from '../../src/components/shared';
import { Colors, Spacing, Radius, FontSize } from '../../src/constants/colors';

const IR_TABLE = [
  { type: 'Renda Fixa > 720 dias', rate: '15%', note: 'Tabela regressiva — menor alíquota' },
  { type: 'Renda Fixa 361-720 dias', rate: '17,5%', note: 'Tabela regressiva' },
  { type: 'Renda Fixa 181-360 dias', rate: '20%', note: 'Tabela regressiva' },
  { type: 'Renda Fixa até 180 dias', rate: '22,5%', note: 'Tabela regressiva — maior alíquota' },
  { type: 'Ações (ganho de capital)', rate: '15%', note: 'Isento se vendas < R$20k/mês' },
  { type: 'FIIs (ganho de capital)', rate: '20%', note: 'Dividendos mensais ISENTOS para PF' },
  { type: 'ETFs de ações', rate: '15%', note: 'DARF mensal; sem isenção' },
  { type: 'LCI/LCA/CRI/CRA', rate: 'ISENTO', note: 'Isenção total para pessoa física' },
  { type: 'Dividendos de ações', rate: 'ISENTO', note: 'Atualmente isento (verificar legislação)' },
  { type: 'PGBL (resgate)', rate: '10-27,5%', note: 'Incide sobre valor total; tabela progressiva/regressiva' },
  { type: 'VGBL (resgate)', rate: '10-27,5%', note: 'Incide só sobre rendimentos' },
];

export default function IRAdvisorModal() {
  const store = usePortfolioStore();
  const [isLoading, setIsLoading] = useState(false);
  const [analysis, setAnalysis] = useState('');

  const deductibleTransactions = detectDeductibleExpenses(
    store.transactions.map(tx => ({
      description: tx.description,
      amount: tx.amount,
      date: tx.date,
    }))
  );

  const deductibleHealth = deductibleTransactions
    .filter(tx => tx.category === 'saude')
    .reduce((sum, tx) => sum + tx.amount, 0);

  const deductibleEducation = deductibleTransactions
    .filter(tx => tx.category === 'educacao')
    .reduce((sum, tx) => sum + tx.amount, 0);

  const deductiblePension = store.realInvestments
    .filter(inv => inv.type === 'RETIREMENT')
    .reduce((sum, inv) => sum + inv.balance, 0);

  const stockSales = store.paperPositions
    .filter(p => p.type === 'stock')
    .reduce((sum, p) => sum + p.currentPrice * p.quantity, 0);

  const handleAnalyze = useCallback(async () => {
    setIsLoading(true);
    setAnalysis('');

    try {
      const suggestion = await analyzeIR(
        [
          ...store.realInvestments.map(inv => ({
            name: inv.name,
            type: inv.type,
            value: inv.balance,
            purchaseDate: inv.lastTransactionDate,
          })),
          ...store.paperPositions.map(pos => ({
            name: pos.name,
            type: pos.type,
            value: pos.currentPrice * pos.quantity,
          })),
        ],
        {
          health: deductibleHealth,
          education: deductibleEducation,
          pension: deductiblePension,
        },
        stockSales,
      );

      setAnalysis(suggestion.content);
      store.addAISuggestion(suggestion);
    } catch (error) {
      Alert.alert('Erro', error instanceof Error ? error.message : 'Falha na análise de IR');
    } finally {
      setIsLoading(false);
    }
  }, [store.realInvestments, store.paperPositions, deductibleHealth, deductibleEducation, deductiblePension, stockSales]);

  const daysToDeadline = () => {
    const now = new Date();
    const deadline = new Date(now.getFullYear(), 3, 30); // April 30
    if (now > deadline) {
      deadline.setFullYear(now.getFullYear() + 1);
    }
    const diff = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>🧾 Imposto de Renda</Text>
      <Text style={styles.subtitle}>
        Análise tributária baseada nos seus investimentos e gastos reais
      </Text>

      {/* Countdown */}
      <Card style={styles.countdownCard}>
        <Text style={styles.countdownIcon}>📅</Text>
        <View style={{ flex: 1 }}>
          <Text style={styles.countdownTitle}>
            Prazo da declaração: {daysToDeadline()} dias
          </Text>
          <Text style={styles.countdownSubtitle}>30 de abril — IRPF</Text>
        </View>
      </Card>

      {/* Detected Deductibles */}
      <Card>
        <SectionHeader title="Gastos Dedutíveis Detectados" subtitle="Via Open Finance" />
        {deductibleTransactions.length === 0 ? (
          <Text style={styles.emptyText}>
            Nenhum gasto dedutível detectado. Conecte sua conta bancária para análise automática.
          </Text>
        ) : (
          <View style={styles.deductiblesList}>
            {deductibleHealth > 0 && (
              <View style={styles.deductibleItem}>
                <Text style={styles.deductibleIcon}>🏥</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.deductibleName}>Saúde</Text>
                  <Text style={styles.deductibleNote}>Dedutível sem limite (modelo completo)</Text>
                </View>
                <Text style={styles.deductibleAmount}>{formatBRLFull(deductibleHealth)}</Text>
              </View>
            )}
            {deductibleEducation > 0 && (
              <View style={styles.deductibleItem}>
                <Text style={styles.deductibleIcon}>📚</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.deductibleName}>Educação</Text>
                  <Text style={styles.deductibleNote}>Limite: R$ 3.561,50/ano por dependente</Text>
                </View>
                <Text style={styles.deductibleAmount}>{formatBRLFull(deductibleEducation)}</Text>
              </View>
            )}
            {deductiblePension > 0 && (
              <View style={styles.deductibleItem}>
                <Text style={styles.deductibleIcon}>🏦</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.deductibleName}>PGBL</Text>
                  <Text style={styles.deductibleNote}>Até 12% da renda bruta anual</Text>
                </View>
                <Text style={styles.deductibleAmount}>{formatBRLFull(deductiblePension)}</Text>
              </View>
            )}
          </View>
        )}
      </Card>

      {/* IR Table */}
      <Card>
        <SectionHeader title="Tabela de IR por Investimento" />
        <View style={styles.irTable}>
          {IR_TABLE.map((row, i) => (
            <View key={i} style={[styles.irRow, i % 2 === 0 && styles.irRowAlt]}>
              <View style={styles.irRowLeft}>
                <Text style={styles.irType}>{row.type}</Text>
                <Text style={styles.irNote}>{row.note}</Text>
              </View>
              <Text style={[
                styles.irRate,
                row.rate === 'ISENTO' ? { color: Colors.success } : { color: Colors.warning }
              ]}>
                {row.rate}
              </Text>
            </View>
          ))}
        </View>
      </Card>

      {/* PGBL Tip */}
      <Card style={styles.pgblCard}>
        <Text style={styles.pgblTitle}>💡 Otimização PGBL</Text>
        <Text style={styles.pgblText}>
          PGBL permite deduzir até 12% da renda bruta anual na declaração completa.
          {'\n\n'}Exemplo: Renda de R$ 200.000/ano → você pode deduzir até R$ 24.000/ano em PGBL.
          Com alíquota de 27,5%, isso gera economia de ~R$ 6.600 em IR por ano.
          {'\n\n'}Esse valor economizado pode ser reinvestido para acelerar sua meta de R$ 3M.
        </Text>
      </Card>

      {/* AI Analysis */}
      <Card>
        <SectionHeader title="Análise Completa com IA" />
        {analysis ? (
          <Text style={styles.analysisText}>{analysis}</Text>
        ) : (
          <Text style={styles.analysisPlaceholder}>
            Clique em "Analisar com Claude" para receber uma análise tributária personalizada baseada nos seus dados reais.
          </Text>
        )}

        {isLoading ? (
          <LoadingSpinner text="Claude analisando sua situação tributária..." />
        ) : (
          <TouchableOpacity style={styles.analyzeBtn} onPress={handleAnalyze}>
            <Text style={styles.analyzeBtnText}>🤖 Analisar com Claude</Text>
          </TouchableOpacity>
        )}
      </Card>

      <Text style={styles.disclaimer}>
        ⚠️ Informações educacionais. Consulte um contador ou advogado tributarista para declaração formal do IRPF.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  title: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  subtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  countdownCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    borderColor: Colors.warning,
    backgroundColor: Colors.warningBg,
  },
  countdownIcon: { fontSize: 24 },
  countdownTitle: { color: Colors.text, fontSize: FontSize.md, fontWeight: '700' },
  countdownSubtitle: { color: Colors.textMuted, fontSize: FontSize.xs },
  emptyText: { color: Colors.textMuted, fontSize: FontSize.sm, textAlign: 'center', padding: Spacing.md },
  deductiblesList: { gap: Spacing.sm },
  deductibleItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  deductibleIcon: { fontSize: 20 },
  deductibleName: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '700' },
  deductibleNote: { color: Colors.textMuted, fontSize: FontSize.xs },
  deductibleAmount: { color: Colors.success, fontSize: FontSize.sm, fontWeight: '700' },
  irTable: { gap: 0 },
  irRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.sm,
    gap: Spacing.sm,
  },
  irRowAlt: { backgroundColor: Colors.bgCardHover, borderRadius: 6 },
  irRowLeft: { flex: 1 },
  irType: { color: Colors.text, fontSize: FontSize.xs, fontWeight: '600' },
  irNote: { color: Colors.textMuted, fontSize: FontSize.xs, marginTop: 1 },
  irRate: { fontSize: FontSize.sm, fontWeight: '800', minWidth: 60, textAlign: 'right' },
  pgblCard: { borderColor: Colors.accentDark, gap: Spacing.sm },
  pgblTitle: { color: Colors.accentLight, fontSize: FontSize.md, fontWeight: '700' },
  pgblText: { color: Colors.text, fontSize: FontSize.sm, lineHeight: 22 },
  analysisText: { color: Colors.text, fontSize: FontSize.sm, lineHeight: 22, marginBottom: Spacing.md },
  analysisPlaceholder: { color: Colors.textMuted, fontSize: FontSize.sm, lineHeight: 20, marginBottom: Spacing.md },
  analyzeBtn: {
    backgroundColor: Colors.accent,
    borderRadius: Radius.md,
    padding: Spacing.md,
    alignItems: 'center',
  },
  analyzeBtnText: { color: '#fff', fontSize: FontSize.md, fontWeight: '800' },
  disclaimer: { color: Colors.textMuted, fontSize: FontSize.xs, textAlign: 'center', lineHeight: 18 },
});
