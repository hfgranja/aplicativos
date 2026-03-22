import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { usePortfolioStore } from '../../src/store/usePortfolioStore';
import { formatBRL, totalAnnualContribution, yearsToGoal } from '../../src/utils/calculations';
import { Card, SectionHeader } from '../../src/components/shared';
import { Colors, Spacing, Radius, FontSize } from '../../src/constants/colors';

const PATHS = [
  {
    id: 1,
    icon: '⏳',
    title: 'Caminho 1 — Manter o fluxo e alongar o prazo',
    subtitle: 'O mais racional',
    isRecommended: false,
    color: Colors.posFixed,
    description: `Manter os R$ 212.000/ano e aceitar o prazo de 10 a 12 anos como o horizonte correto.

Meta real: R$ 3.000.000 (valor corrigido)
Prazo provável: 10 a 12 anos
Estratégia: disciplina de aporte + carteira focada em retorno real

Este caminho é a base. A maioria das pessoas subestima quanto disciplina vale.`,
    pros: [
      'Menor pressão sobre a geração de renda',
      'Permite foco em qualidade de vida atual',
      'Fluxo já está funcionando',
    ],
    cons: [
      '10-12 anos é um prazo longo',
      'Depende da disciplina ao longo do tempo',
      'Vulnerável a mudanças de vida não planejadas',
    ],
    yearsEstimate: '10-12 anos',
    contribution: 212000,
  },
  {
    id: 2,
    icon: '🚀',
    title: 'Caminho 2 — Manter 6 anos e aumentar brutalmente o caixa',
    subtitle: 'Muda a conversa para geração de renda',
    isRecommended: false,
    color: Colors.growth,
    description: `Para atingir R$ 3M em 6 anos, você precisaria aumentar fortemente os aportes anuais.

Estimativa: ~R$ 380-430k/ano (quase dobrar o esforço)
A conversa deixa de ser sobre investimento e passa a ser sobre geração de renda.

Isso pode ser viável com: promoção, mudança de carreira, venda de ativo, negócio próprio.`,
    pros: [
      'Meta alcançada mais rápido',
      'Menor exposição a imprevistos de longo prazo',
      'Momentum financeiro mais forte',
    ],
    cons: [
      'Exige quase dobrar a geração de caixa',
      'Pressão alta sobre renda ativa',
      'Alta dependência de tudo correr bem',
    ],
    yearsEstimate: '~6 anos',
    contribution: 400000,
  },
  {
    id: 3,
    icon: '🎯',
    title: 'Caminho 3 — Híbrido (o melhor dos mundos)',
    subtitle: '⭐ Recomendado',
    isRecommended: true,
    color: Colors.accent,
    description: `Mantém os R$ 212k/ano base e cria uma meta de capital extra anual de R$ 100-150k proveniente de fontes adicionais.

Fontes de capital extra: bônus, PLR, venda de ativo, consultoria, advisory, renda paralela, freelance.

Com R$ 100k extra/ano: bate R$ 3M em ~10-11 anos
Com R$ 150k extra/ano: bate R$ 3M em ~9-10 anos

Não depende de sorte. Depende de criação de valor ativo.`,
    pros: [
      'Equilíbrio entre esforço atual e prazo',
      'Cada R$ extra muda significativamente o resultado',
      'Diversifica fontes de renda',
      'Aceita que nem todo ano será igual',
    ],
    cons: [
      'Requer criatividade para gerar renda extra',
      'Pressão moderada sobre tempo e energia',
      'Resultado depende da execução',
    ],
    yearsEstimate: '9-11 anos',
    contribution: 312000,
  },
];

export default function StrategyModal() {
  const store = usePortfolioStore();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>🗺️ Estratégia</Text>
      <Text style={styles.subtitle}>
        3 caminhos para R$ 3M — escolha o seu
      </Text>

      {/* Summary */}
      <Card style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>Sua situação atual</Text>
        <View style={styles.summaryItems}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Aporte mensal</Text>
            <Text style={styles.summaryValue}>{formatBRL(store.monthlyContribution)}</Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Aporte anual</Text>
            <Text style={styles.summaryValue}>{formatBRL(store.annualContribution)}</Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Total/ano</Text>
            <Text style={[styles.summaryValue, { color: Colors.accent }]}>
              {formatBRL(totalAnnualContribution(store.monthlyContribution, store.annualContribution))}
            </Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Meta</Text>
            <Text style={styles.summaryValue}>{formatBRL(store.goal)}</Text>
          </View>
        </View>
      </Card>

      {/* 3 Paths */}
      {PATHS.map(path => (
        <Card
          key={path.id}
          style={[
            styles.pathCard,
            { borderColor: path.isRecommended ? path.color : Colors.border },
            path.isRecommended && styles.pathCardRecommended,
          ]}
        >
          {path.isRecommended && (
            <View style={[styles.recommendedBadge, { backgroundColor: path.color }]}>
              <Text style={styles.recommendedText}>⭐ Recomendado</Text>
            </View>
          )}

          <View style={styles.pathHeader}>
            <Text style={styles.pathIcon}>{path.icon}</Text>
            <View style={{ flex: 1 }}>
              <Text style={[styles.pathTitle, { color: path.color }]}>{path.title}</Text>
              <Text style={styles.pathSubtitle}>{path.subtitle}</Text>
            </View>
          </View>

          <View style={styles.pathMeta}>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>Prazo estimado</Text>
              <Text style={[styles.metaValue, { color: path.color }]}>{path.yearsEstimate}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>Aporte necessário/ano</Text>
              <Text style={[styles.metaValue, { color: path.color }]}>{formatBRL(path.contribution)}</Text>
            </View>
          </View>

          <Text style={styles.pathDescription}>{path.description}</Text>

          <View style={styles.prosConsGrid}>
            <View style={styles.pros}>
              <Text style={styles.prosTitle}>✅ Prós</Text>
              {path.pros.map((pro, i) => (
                <Text key={i} style={styles.proItem}>• {pro}</Text>
              ))}
            </View>
            <View style={styles.cons}>
              <Text style={styles.consTitle}>⚠️ Contras</Text>
              {path.cons.map((con, i) => (
                <Text key={i} style={styles.conItem}>• {con}</Text>
              ))}
            </View>
          </View>
        </Card>
      ))}

      {/* Recommended Portfolio */}
      <Card style={styles.portfolioCard}>
        <SectionHeader title="📊 Carteira Sugerida para a Meta" />
        <Text style={styles.portfolioSubtitle}>Para horizonte de 10-12 anos:</Text>

        {[
          { label: 'IPCA+', pct: '50-60%', color: Colors.ipcaPlus, desc: 'Tesouro IPCA+, CDB IPCA+, Debêntures. Protege o poder de compra.' },
          { label: 'Pós-fixado', pct: '20-30%', color: Colors.posFixed, desc: 'Tesouro SELIC, LCI/LCA. Liquidez e segurança.' },
          { label: 'Crescimento', pct: '15-25%', color: Colors.growth, desc: 'ETFs (BOVA11, IVVB11), FIIs, ações de qualidade.' },
        ].map(item => (
          <View key={item.label} style={styles.portfolioItem}>
            <View style={[styles.portfolioBar, { backgroundColor: item.color }]} />
            <View style={{ flex: 1 }}>
              <View style={styles.portfolioLabelRow}>
                <Text style={[styles.portfolioLabel, { color: item.color }]}>{item.label}</Text>
                <Text style={[styles.portfolioPct, { color: item.color }]}>{item.pct}</Text>
              </View>
              <Text style={styles.portfolioDesc}>{item.desc}</Text>
            </View>
          </View>
        ))}
      </Card>

      {/* Direct Recommendation */}
      <Card style={styles.finalCard}>
        <Text style={styles.finalTitle}>💬 Minha Recomendação Direta</Text>
        <Text style={styles.finalText}>
          Trate 6 anos como meta esticada demais.{'\n'}
          Trate 10 a 12 anos como plano vencedor.{'\n\n'}
          Use os próximos 24 meses para elevar geração de caixa, não só retorno de carteira.{'\n\n'}
          {"Investimento bom ajuda.\nRenda forte acelera.\nDisciplina é o que faz a mágica parecer inteligência superior."}
        </Text>
      </Card>

      {/* Checklist */}
      <Card>
        <SectionHeader title="✅ Próximos 24 meses — Checklist" />
        {[
          'Automatizar o aporte mensal de R$ 1.000',
          'Confirmar alocação: 55% IPCA+, 25% pós-fixado, 20% crescimento',
          'Conectar conta íon/BTG/XP para monitoramento real',
          'Identificar 1-2 fontes de renda extra (PLR, consultoria, bônus)',
          'Revisar PGBL: calcular contribuição ideal para dedução IR',
          'Criar meta de capital extra anual (R$ 100-150k)',
          'Revisar carteira a cada 6 meses com IA Advisor',
        ].map((item, i) => (
          <View key={i} style={styles.checklistItem}>
            <Text style={styles.checklistBullet}>☐</Text>
            <Text style={styles.checklistText}>{item}</Text>
          </View>
        ))}
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  title: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  subtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  summaryCard: { gap: Spacing.sm },
  summaryTitle: { color: Colors.textSecondary, fontSize: FontSize.sm, fontWeight: '700' },
  summaryItems: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.md },
  summaryItem: { gap: 2 },
  summaryLabel: { color: Colors.textMuted, fontSize: FontSize.xs },
  summaryValue: { color: Colors.text, fontSize: FontSize.md, fontWeight: '700' },
  pathCard: { borderWidth: 1, gap: Spacing.md, position: 'relative', overflow: 'hidden' },
  pathCardRecommended: { backgroundColor: `${Colors.accent}08` },
  recommendedBadge: {
    position: 'absolute',
    top: 0,
    right: 0,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderBottomLeftRadius: Radius.sm,
  },
  recommendedText: { color: '#fff', fontSize: FontSize.xs, fontWeight: '700' },
  pathHeader: { flexDirection: 'row', gap: Spacing.sm, alignItems: 'flex-start', marginTop: Spacing.xs },
  pathIcon: { fontSize: 28 },
  pathTitle: { fontSize: FontSize.md, fontWeight: '800' },
  pathSubtitle: { color: Colors.textMuted, fontSize: FontSize.xs, marginTop: 2 },
  pathMeta: { flexDirection: 'row', gap: Spacing.xl },
  metaItem: { gap: 2 },
  metaLabel: { color: Colors.textMuted, fontSize: FontSize.xs },
  metaValue: { fontSize: FontSize.md, fontWeight: '800' },
  pathDescription: { color: Colors.text, fontSize: FontSize.sm, lineHeight: 22 },
  prosConsGrid: { flexDirection: 'row', gap: Spacing.md },
  pros: { flex: 1, gap: 4 },
  cons: { flex: 1, gap: 4 },
  prosTitle: { color: Colors.success, fontSize: FontSize.xs, fontWeight: '700', marginBottom: 2 },
  consTitle: { color: Colors.warning, fontSize: FontSize.xs, fontWeight: '700', marginBottom: 2 },
  proItem: { color: Colors.textSecondary, fontSize: FontSize.xs, lineHeight: 18 },
  conItem: { color: Colors.textSecondary, fontSize: FontSize.xs, lineHeight: 18 },
  portfolioCard: { gap: Spacing.md },
  portfolioSubtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  portfolioItem: { flexDirection: 'row', gap: Spacing.sm, alignItems: 'flex-start' },
  portfolioBar: { width: 4, borderRadius: 2, marginTop: 4, alignSelf: 'stretch', minHeight: 36 },
  portfolioLabelRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  portfolioLabel: { fontSize: FontSize.sm, fontWeight: '700' },
  portfolioPct: { fontSize: FontSize.sm, fontWeight: '700' },
  portfolioDesc: { color: Colors.textSecondary, fontSize: FontSize.xs, lineHeight: 18, marginTop: 2 },
  finalCard: { borderColor: Colors.accentDark, gap: Spacing.sm },
  finalTitle: { color: Colors.accentLight, fontSize: FontSize.md, fontWeight: '700' },
  finalText: { color: Colors.text, fontSize: FontSize.sm, lineHeight: 24, fontStyle: 'italic' },
  checklistItem: { flexDirection: 'row', gap: Spacing.sm, paddingVertical: 4 },
  checklistBullet: { color: Colors.accent, fontSize: FontSize.md },
  checklistText: { color: Colors.text, fontSize: FontSize.sm, flex: 1, lineHeight: 22 },
});
