import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TextInput, TouchableOpacity, Alert, Switch,
} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { usePortfolioStore } from '../src/store/usePortfolioStore';
import { savePluggyCredentials, getPluggyCredentials } from '../src/services/pluggy';
import { formatBRL } from '../src/utils/calculations';
import { Card, SectionHeader } from '../src/components/shared';
import { Colors, Spacing, Radius, FontSize } from '../src/constants/colors';

export default function SettingsScreen() {
  const store = usePortfolioStore();

  // Claude API key
  const [claudeKey, setClaudeKey] = useState('');
  const [showClaudeKey, setShowClaudeKey] = useState(false);
  const [claudeKeySaved, setClaudeKeySaved] = useState(false);

  // Pluggy credentials
  const [pluggyClientId, setPluggyClientId] = useState('');
  const [pluggySecret, setPluggySecret] = useState('');
  const [showPluggySecret, setShowPluggySecret] = useState(false);
  const [pluggyCredsSaved, setPluggyCredsSaved] = useState(false);

  // Plan settings
  const [localMonthly, setLocalMonthly] = useState(store.monthlyContribution.toString());
  const [localAnnual, setLocalAnnual] = useState(store.annualContribution.toString());
  const [localExtra, setLocalExtra] = useState(store.extraAnnualContribution.toString());
  const [localGoal, setLocalGoal] = useState(store.goal.toString());

  useEffect(() => {
    const loadKeys = async () => {
      const key = await SecureStore.getItemAsync('claude_api_key');
      if (key) {
        setClaudeKey('•'.repeat(20));
        setClaudeKeySaved(true);
      }

      const pluggyCreds = await getPluggyCredentials();
      if (pluggyCreds) {
        setPluggyClientId(pluggyCreds.clientId);
        setPluggySecret('•'.repeat(20));
        setPluggyCredsSaved(true);
      }
    };
    loadKeys();
  }, []);

  const saveClaudeKey = useCallback(async () => {
    if (!claudeKey.trim() || claudeKey.startsWith('•')) {
      Alert.alert('Erro', 'Informe uma chave válida');
      return;
    }

    await SecureStore.setItemAsync('claude_api_key', claudeKey.trim());
    setClaudeKeySaved(true);
    setClaudeKey('•'.repeat(20));
    Alert.alert('✅ Salvo', 'Chave Claude salva com segurança (SecureStore)');
  }, [claudeKey]);

  const clearClaudeKey = useCallback(async () => {
    await SecureStore.deleteItemAsync('claude_api_key');
    setClaudeKey('');
    setClaudeKeySaved(false);
    Alert.alert('Removido', 'Chave Claude removida');
  }, []);

  const savePluggyCreds = useCallback(async () => {
    if (!pluggyClientId.trim()) {
      Alert.alert('Erro', 'Informe o Client ID da Pluggy');
      return;
    }
    if (!pluggySecret.trim() || pluggySecret.startsWith('•')) {
      Alert.alert('Erro', 'Informe o Client Secret da Pluggy');
      return;
    }

    await savePluggyCredentials({ clientId: pluggyClientId.trim(), clientSecret: pluggySecret.trim() });
    setPluggyCredsSaved(true);
    setPluggySecret('•'.repeat(20));
    Alert.alert('✅ Salvo', 'Credenciais Pluggy salvas com segurança');
  }, [pluggyClientId, pluggySecret]);

  const savePlanSettings = useCallback(() => {
    const monthly = parseInt(localMonthly, 10) || 0;
    const annual = parseInt(localAnnual, 10) || 0;
    const extra = parseInt(localExtra, 10) || 0;
    const goal = parseInt(localGoal.replace(/\D/g, ''), 10) || 3000000;

    store.setContributions(monthly, annual, extra);
    Alert.alert('✅ Salvo', `Aportes: R$ ${formatBRL(monthly)}/mês + R$ ${formatBRL(annual)}/ano\nMeta: R$ ${formatBRL(goal)}`);
  }, [localMonthly, localAnnual, localExtra, localGoal]);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Configurações</Text>

      {/* Plan Settings */}
      <Card>
        <SectionHeader title="Plano de Investimento" />

        {[
          { label: 'Aporte Mensal (R$)', value: localMonthly, onChange: setLocalMonthly, placeholder: '1000' },
          { label: 'Aporte Anual (R$)', value: localAnnual, onChange: setLocalAnnual, placeholder: '200000' },
          { label: 'Aporte Extra Anual (R$)', value: localExtra, onChange: setLocalExtra, placeholder: '0' },
          { label: 'Meta Final (R$)', value: localGoal, onChange: setLocalGoal, placeholder: '3000000' },
        ].map(field => (
          <View key={field.label} style={styles.formGroup}>
            <Text style={styles.formLabel}>{field.label}</Text>
            <TextInput
              style={styles.formInput}
              value={field.value}
              onChangeText={field.onChange}
              placeholder={field.placeholder}
              placeholderTextColor={Colors.textMuted}
              keyboardType="numeric"
            />
          </View>
        ))}

        <TouchableOpacity style={styles.saveBtn} onPress={savePlanSettings}>
          <Text style={styles.saveBtnText}>💾 Salvar Plano</Text>
        </TouchableOpacity>
      </Card>

      {/* Claude API Key */}
      <Card>
        <SectionHeader
          title="🤖 Claude API Key"
          subtitle={claudeKeySaved ? '✅ Configurada' : '⭕ Não configurada'}
        />
        <Text style={styles.apiDesc}>
          Necessária para análises de portfólio, gastos, IR e chat.
          Obtenha em: console.anthropic.com
        </Text>
        <View style={styles.formGroup}>
          <Text style={styles.formLabel}>API Key</Text>
          <View style={styles.passwordRow}>
            <TextInput
              style={[styles.formInput, { flex: 1 }]}
              value={claudeKey}
              onChangeText={v => { setClaudeKey(v); setClaudeKeySaved(false); }}
              placeholder="sk-ant-..."
              placeholderTextColor={Colors.textMuted}
              secureTextEntry={!showClaudeKey}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <TouchableOpacity
              style={styles.eyeBtn}
              onPress={() => setShowClaudeKey(v => !v)}
            >
              <Text style={styles.eyeBtnText}>{showClaudeKey ? '🙈' : '👁️'}</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.btnRow}>
          <TouchableOpacity style={styles.saveBtn} onPress={saveClaudeKey}>
            <Text style={styles.saveBtnText}>💾 Salvar</Text>
          </TouchableOpacity>
          {claudeKeySaved && (
            <TouchableOpacity style={styles.dangerBtn} onPress={clearClaudeKey}>
              <Text style={styles.dangerBtnText}>🗑️ Remover</Text>
            </TouchableOpacity>
          )}
        </View>
      </Card>

      {/* Pluggy Credentials */}
      <Card>
        <SectionHeader
          title="🏦 Pluggy — Open Finance"
          subtitle={pluggyCredsSaved ? '✅ Configurada' : '⭕ Não configurada'}
        />
        <Text style={styles.apiDesc}>
          Necessário para conectar sua conta íon, Nubank, BTG, XP e outras.
          Crie sua conta gratuita em: pluggy.ai
        </Text>

        <View style={styles.formGroup}>
          <Text style={styles.formLabel}>Client ID</Text>
          <TextInput
            style={styles.formInput}
            value={pluggyClientId}
            onChangeText={setPluggyClientId}
            placeholder="seu-client-id"
            placeholderTextColor={Colors.textMuted}
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.formLabel}>Client Secret</Text>
          <View style={styles.passwordRow}>
            <TextInput
              style={[styles.formInput, { flex: 1 }]}
              value={pluggySecret}
              onChangeText={v => { setPluggySecret(v); setPluggyCredsSaved(false); }}
              placeholder="seu-client-secret"
              placeholderTextColor={Colors.textMuted}
              secureTextEntry={!showPluggySecret}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <TouchableOpacity
              style={styles.eyeBtn}
              onPress={() => setShowPluggySecret(v => !v)}
            >
              <Text style={styles.eyeBtnText}>{showPluggySecret ? '🙈' : '👁️'}</Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity style={styles.saveBtn} onPress={savePluggyCreds}>
          <Text style={styles.saveBtnText}>💾 Salvar Credenciais</Text>
        </TouchableOpacity>
      </Card>

      {/* About */}
      <Card>
        <SectionHeader title="Sobre o App" />
        <Text style={styles.aboutText}>
          Portfólio de Investimentos v1.0.0{'\n'}
          React Native + Expo SDK 53{'\n\n'}
          Integrations:{'\n'}
          • Claude AI (Anthropic) — análises financeiras{'\n'}
          • Pluggy — Open Finance Brasil{'\n'}
          • Brapi.dev — cotações B3{'\n'}
          • Tesouro Direto — API oficial{'\n\n'}
          Paper trading é simulação educacional.{'\n'}
          Consulte um profissional antes de investir.
        </Text>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  title: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
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
  passwordRow: { flexDirection: 'row', gap: Spacing.sm, alignItems: 'center' },
  eyeBtn: { padding: Spacing.sm },
  eyeBtnText: { fontSize: 20 },
  apiDesc: { color: Colors.textMuted, fontSize: FontSize.xs, lineHeight: 18, marginBottom: Spacing.sm },
  btnRow: { flexDirection: 'row', gap: Spacing.sm },
  saveBtn: {
    flex: 1,
    backgroundColor: Colors.accent,
    borderRadius: Radius.md,
    padding: Spacing.md,
    alignItems: 'center',
  },
  saveBtnText: { color: '#fff', fontSize: FontSize.sm, fontWeight: '800' },
  dangerBtn: {
    backgroundColor: Colors.dangerBg,
    borderRadius: Radius.md,
    padding: Spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.danger,
  },
  dangerBtnText: { color: Colors.danger, fontSize: FontSize.sm, fontWeight: '700' },
  aboutText: { color: Colors.textSecondary, fontSize: FontSize.sm, lineHeight: 22 },
});
