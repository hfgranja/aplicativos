import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TextInput, TouchableOpacity,
  KeyboardAvoidingView, Platform, RefreshControl,
} from 'react-native';
import { router } from 'expo-router';
import { usePortfolioStore, selectTotalNetWorth } from '../../src/store/usePortfolioStore';
import { chat, analyzePortfolio, analyzeSpending, generateMarketAlerts, ChatMessage } from '../../src/services/claudeAI';
import { summarizeByCategory } from '../../src/utils/categorizer';
import { formatBRL } from '../../src/utils/calculations';
import { Card, SectionHeader, LoadingSpinner, EmptyState } from '../../src/components/shared';
import { Colors, Spacing, Radius, FontSize } from '../../src/constants/colors';

const QUICK_ACTIONS = [
  { id: 'portfolio', label: '📊 Analise meu portfólio', message: 'Analise meu portfólio atual e me dê 3 sugestões acionáveis para otimizar em relação à meta de R$ 3M.' },
  { id: 'spending', label: '💰 Onde economizar?', message: 'Analise meus gastos e me diga onde posso reduzir despesas para acelerar minha meta. Inclua o impacto de cada redução no prazo para atingir R$ 3M.' },
  { id: 'market', label: '📈 Oportunidades agora', message: 'Com base nos dados de mercado atuais (SELIC, IPCA, Ibovespa, Tesouro Direto), quais são as melhores oportunidades de investimento para o meu perfil?' },
  { id: 'scenarios', label: '🎯 Comparar cenários', message: 'Compare os 4 cenários de retorno (2%, 4%, 6%, 8% real) para a minha situação atual. Qual é o mais realista e o que preciso fazer para alcançá-lo?' },
  { id: 'ir', label: '🧾 Imposto de Renda', message: 'Analise minha situação completa de IR: otimização PGBL, gastos dedutíveis, isenções e estratégia tributária para maximizar eficiência fiscal.' },
  { id: 'strategy', label: '🗺️ Minha estratégia', message: 'Descreva a melhor estratégia para eu atingir R$ 3M considerando meus aportes atuais, carteira recomendada e os 3 caminhos disponíveis.' },
];

export default function AIAdvisorScreen() {
  const store = usePortfolioStore();
  const totalValue = selectTotalNetWorth(store);

  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);

  const categories = summarizeByCategory(
    store.transactions.map(tx => ({
      description: tx.description,
      amount: tx.amount,
      type: tx.type,
    }))
  );

  const sendMessage = useCallback(async (messageText: string) => {
    if (!messageText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: messageText.trim(),
      timestamp: new Date(),
    };

    store.addChatMessage(userMessage);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await chat(
        messageText.trim(),
        store.chatHistory,
        {
          portfolioValue: totalValue,
          marketIndices: store.marketIndices || undefined,
        }
      );

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };

      store.addChatMessage(assistantMessage);

      // Scroll to bottom
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Erro: ${error instanceof Error ? error.message : 'Falha na comunicação com Claude'}. Verifique sua API key em Configurações.`,
        timestamp: new Date(),
      };
      store.addChatMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, store.chatHistory, totalValue, store.marketIndices]);

  const handleQuickAction = useCallback((actionId: string, message: string) => {
    if (actionId === 'ir') {
      router.push('/modal/ir-advisor');
      return;
    }
    if (actionId === 'strategy') {
      router.push('/modal/strategy');
      return;
    }
    sendMessage(message);
  }, [sendMessage]);

  const refreshAlerts = useCallback(async () => {
    if (store.marketIndices && store.tesouroBonds.length > 0) {
      const alerts = await generateMarketAlerts(
        { value: totalValue, allocation: store.allocation },
        store.marketIndices,
        store.tesouroBonds,
      );
      store.setMarketAlerts(alerts);
    }
  }, [totalValue, store.marketIndices, store.tesouroBonds]);

  useEffect(() => {
    refreshAlerts();
  }, []);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      <ScrollView
        ref={scrollViewRef}
        style={styles.scrollView}
        contentContainerStyle={styles.content}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>IA Advisor</Text>
          <Text style={styles.headerSubtitle}>Claude — especialista em finanças BR</Text>
        </View>

        {/* Market Alerts */}
        {store.marketAlerts.length > 0 && (
          <Card style={styles.alertsCard}>
            <SectionHeader title="🔔 Alertas" />
            {store.marketAlerts.map((alert, i) => (
              <View key={i} style={styles.alertItem}>
                <Text style={styles.alertBullet}>•</Text>
                <Text style={styles.alertText}>{alert}</Text>
              </View>
            ))}
          </Card>
        )}

        {/* Quick Actions */}
        <Card>
          <SectionHeader title="Ações Rápidas" />
          <View style={styles.quickActionsGrid}>
            {QUICK_ACTIONS.map(action => (
              <TouchableOpacity
                key={action.id}
                style={styles.quickAction}
                onPress={() => handleQuickAction(action.id, action.message)}
                disabled={isLoading}
              >
                <Text style={styles.quickActionText}>{action.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </Card>

        {/* Chat History */}
        {store.chatHistory.length === 0 ? (
          <EmptyState
            icon="🤖"
            title="Converse com seu advisor"
            description="Faça qualquer pergunta sobre investimentos, gastos, imposto de renda ou estratégia financeira. Seu advisor tem acesso aos seus dados reais."
          />
        ) : (
          <View style={styles.chatContainer}>
            <View style={styles.chatHeader}>
              <Text style={styles.chatTitle}>Conversa</Text>
              <TouchableOpacity onPress={store.clearChatHistory}>
                <Text style={styles.clearBtn}>Limpar</Text>
              </TouchableOpacity>
            </View>

            {store.chatHistory.map((msg, index) => (
              <View
                key={index}
                style={[
                  styles.messageBubble,
                  msg.role === 'user' ? styles.userBubble : styles.assistantBubble,
                ]}
              >
                {msg.role === 'assistant' && (
                  <Text style={styles.messageRole}>🤖 Claude</Text>
                )}
                <Text style={[
                  styles.messageText,
                  msg.role === 'user' ? styles.userText : styles.assistantText,
                ]}>
                  {msg.content}
                </Text>
                <Text style={styles.messageTime}>
                  {msg.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </Text>
              </View>
            ))}

            {isLoading && (
              <View style={[styles.messageBubble, styles.assistantBubble]}>
                <Text style={styles.messageRole}>🤖 Claude</Text>
                <View style={styles.typingIndicator}>
                  <Text style={styles.typingDot}>●</Text>
                  <Text style={[styles.typingDot, styles.typingDot2]}>●</Text>
                  <Text style={[styles.typingDot, styles.typingDot3]}>●</Text>
                </View>
              </View>
            )}
          </View>
        )}

        {/* Context Info */}
        <Card style={styles.contextCard}>
          <Text style={styles.contextTitle}>📋 Contexto disponível para o advisor</Text>
          <View style={styles.contextItems}>
            <Text style={styles.contextItem}>✅ Plano: R$ 1k/mês + R$ 200k/ano, meta R$ 3M</Text>
            <Text style={styles.contextItem}>
              {store.marketIndices ? '✅' : '⭕'} Dados de mercado (SELIC, IPCA, Ibovespa)
            </Text>
            <Text style={styles.contextItem}>
              {store.tesouroBonds.length > 0 ? '✅' : '⭕'} Tesouro Direto ({store.tesouroBonds.length} títulos)
            </Text>
            <Text style={styles.contextItem}>
              {store.transactions.length > 0 ? '✅' : '⭕'} Transações bancárias ({store.transactions.length} itens)
            </Text>
            <Text style={styles.contextItem}>
              {store.realInvestments.length > 0 ? '✅' : '⭕'} Investimentos reais ({store.realInvestments.length} posições)
            </Text>
          </View>
          <TouchableOpacity onPress={() => router.push('/settings')} style={styles.configBtn}>
            <Text style={styles.configBtnText}>⚙️ Configurar API Keys</Text>
          </TouchableOpacity>
        </Card>
      </ScrollView>

      {/* Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Faça uma pergunta..."
          placeholderTextColor={Colors.textMuted}
          multiline
          maxLength={1000}
          editable={!isLoading}
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!inputText.trim() || isLoading) && styles.sendBtnDisabled]}
          onPress={() => sendMessage(inputText)}
          disabled={!inputText.trim() || isLoading}
        >
          <Text style={styles.sendBtnText}>↑</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  scrollView: { flex: 1 },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  header: { gap: 4 },
  headerTitle: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  headerSubtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  alertsCard: { borderColor: Colors.warning, gap: Spacing.sm },
  alertItem: { flexDirection: 'row', gap: Spacing.sm },
  alertBullet: { color: Colors.warning, fontSize: FontSize.md },
  alertText: { color: Colors.text, fontSize: FontSize.sm, flex: 1, lineHeight: 20 },
  quickActionsGrid: { gap: Spacing.sm },
  quickAction: {
    backgroundColor: Colors.bgCardHover,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.sm + 2,
  },
  quickActionText: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '600' },
  chatContainer: { gap: Spacing.sm },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  chatTitle: { color: Colors.text, fontSize: FontSize.md, fontWeight: '700' },
  clearBtn: { color: Colors.danger, fontSize: FontSize.sm },
  messageBubble: {
    borderRadius: Radius.md,
    padding: Spacing.md,
    gap: 6,
    maxWidth: '95%',
  },
  userBubble: {
    backgroundColor: Colors.accentBg,
    borderWidth: 1,
    borderColor: Colors.accentDark,
    alignSelf: 'flex-end',
  },
  assistantBubble: {
    backgroundColor: Colors.bgCard,
    borderWidth: 1,
    borderColor: Colors.border,
    alignSelf: 'flex-start',
  },
  messageRole: { color: Colors.accentLight, fontSize: FontSize.xs, fontWeight: '700' },
  messageText: { fontSize: FontSize.sm, lineHeight: 22 },
  userText: { color: Colors.text },
  assistantText: { color: Colors.text },
  messageTime: { color: Colors.textMuted, fontSize: FontSize.xs, alignSelf: 'flex-end' },
  typingIndicator: { flexDirection: 'row', gap: 4 },
  typingDot: { color: Colors.accent, fontSize: 16 },
  typingDot2: { opacity: 0.6 },
  typingDot3: { opacity: 0.3 },
  contextCard: { borderColor: Colors.border, gap: Spacing.sm },
  contextTitle: { color: Colors.textSecondary, fontSize: FontSize.sm, fontWeight: '700' },
  contextItems: { gap: 4 },
  contextItem: { color: Colors.textMuted, fontSize: FontSize.xs, lineHeight: 18 },
  configBtn: {
    backgroundColor: Colors.bgCardHover,
    borderRadius: Radius.sm,
    padding: Spacing.sm,
    alignItems: 'center',
    marginTop: Spacing.xs,
  },
  configBtnText: { color: Colors.accent, fontSize: FontSize.sm, fontWeight: '600' },
  inputContainer: {
    flexDirection: 'row',
    gap: Spacing.sm,
    padding: Spacing.md,
    backgroundColor: Colors.bgCard,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    backgroundColor: Colors.bgInput,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    color: Colors.text,
    fontSize: FontSize.sm,
    padding: Spacing.sm,
    maxHeight: 120,
  },
  sendBtn: {
    backgroundColor: Colors.accent,
    borderRadius: Radius.full,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendBtnDisabled: { backgroundColor: Colors.bgCardHover, borderWidth: 1, borderColor: Colors.border },
  sendBtnText: { color: '#fff', fontSize: FontSize.lg, fontWeight: '800' },
});
