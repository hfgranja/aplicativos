import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert, Linking,
} from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import { router } from 'expo-router';
import { usePortfolioStore } from '../../src/store/usePortfolioStore';
import { createConnectToken, getItems, deleteItem, PluggyItem, SUPPORTED_INSTITUTIONS } from '../../src/services/pluggy';
import { Card, LoadingSpinner, SectionHeader, EmptyState } from '../../src/components/shared';
import { Colors, Spacing, Radius, FontSize } from '../../src/constants/colors';

export default function ConnectBankModal() {
  const store = usePortfolioStore();
  const [connectedItems, setConnectedItems] = useState<PluggyItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingItems, setIsLoadingItems] = useState(true);

  const loadConnectedItems = useCallback(async () => {
    setIsLoadingItems(true);
    try {
      const items = await getItems();
      setConnectedItems(items);
      // Sync item IDs to store
      for (const item of items) {
        store.addPluggyItem(item.id);
      }
    } catch {
      // no-op — might not have credentials yet
    } finally {
      setIsLoadingItems(false);
    }
  }, []);

  useEffect(() => {
    loadConnectedItems();
  }, []);

  const handleConnect = async () => {
    setIsLoading(true);
    try {
      const connectToken = await createConnectToken();

      // Open Pluggy Connect Widget in browser
      const pluggyConnectUrl = `https://connect.pluggy.ai/?connectToken=${connectToken}`;
      const result = await WebBrowser.openBrowserAsync(pluggyConnectUrl, {
        controlsColor: Colors.accent,
        toolbarColor: Colors.bgCard,
      });

      // After closing, reload items
      await loadConnectedItems();
      await store.refreshOpenFinance();

    } catch (error) {
      Alert.alert(
        'Erro',
        error instanceof Error ? error.message : 'Falha ao conectar. Verifique suas credenciais Pluggy em Configurações.',
        [
          { text: 'Configurações', onPress: () => router.push('/settings') },
          { text: 'OK' },
        ]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = async (item: PluggyItem) => {
    Alert.alert(
      'Desconectar',
      `Deseja remover a conexão com ${item.institutionName}?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Desconectar',
          style: 'destructive',
          onPress: async () => {
            await deleteItem(item.id);
            store.removePluggyItem(item.id);
            await loadConnectedItems();
          },
        },
      ]
    );
  };

  const getStatusColor = (status: PluggyItem['status']) => {
    switch (status) {
      case 'UPDATED': return Colors.success;
      case 'UPDATING': return Colors.warning;
      case 'LOGIN_ERROR': return Colors.danger;
      default: return Colors.textMuted;
    }
  };

  const getStatusLabel = (status: PluggyItem['status']) => {
    switch (status) {
      case 'UPDATED': return 'Sincronizado';
      case 'UPDATING': return 'Atualizando...';
      case 'LOGIN_ERROR': return 'Erro de login';
      case 'WAITING_USER_INPUT': return 'Aguardando';
      default: return 'Erro';
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Conectar Banco</Text>
      <Text style={styles.subtitle}>
        Open Finance Brasil — seus dados reais, com sua autorização
      </Text>

      {/* Security Note */}
      <Card style={styles.securityCard}>
        <Text style={styles.securityIcon}>🔒</Text>
        <View style={{ flex: 1 }}>
          <Text style={styles.securityTitle}>Seus dados são seus</Text>
          <Text style={styles.securityDesc}>
            A conexão usa o Open Finance Brasil regulamentado pelo BACEN.
            Nunca compartilhamos ou armazenamos senhas. Apenas leitura — sem transferências.
          </Text>
        </View>
      </Card>

      {/* Supported Banks */}
      <Card>
        <SectionHeader title="Instituições suportadas" />
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.institutionsList}>
            {SUPPORTED_INSTITUTIONS.filter(i => i.popular).map(inst => (
              <View key={inst.id} style={styles.institutionChip}>
                <Text style={styles.institutionLogo}>{inst.logo}</Text>
                <Text style={styles.institutionName}>{inst.name.split(' ')[0]}</Text>
              </View>
            ))}
          </View>
        </ScrollView>
        <Text style={styles.moreText}>+{SUPPORTED_INSTITUTIONS.filter(i => !i.popular).length} outras instituições</Text>
      </Card>

      {/* Connected Items */}
      <Card>
        <SectionHeader
          title="Contas Conectadas"
          subtitle={isLoadingItems ? 'Carregando...' : `${connectedItems.length} conexões ativas`}
        />
        {isLoadingItems ? (
          <LoadingSpinner text="Verificando conexões..." />
        ) : connectedItems.length === 0 ? (
          <Text style={styles.noConnectionsText}>
            Nenhuma conta conectada ainda. Conecte sua primeira instituição abaixo.
          </Text>
        ) : (
          <View style={styles.itemsList}>
            {connectedItems.map(item => (
              <View key={item.id} style={styles.itemRow}>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{item.institutionName}</Text>
                  <View style={styles.itemStatus}>
                    <View style={[styles.statusDot, { backgroundColor: getStatusColor(item.status) }]} />
                    <Text style={[styles.statusLabel, { color: getStatusColor(item.status) }]}>
                      {getStatusLabel(item.status)}
                    </Text>
                  </View>
                  {item.lastUpdatedAt && (
                    <Text style={styles.lastUpdate}>
                      Última atualização: {new Date(item.lastUpdatedAt).toLocaleDateString('pt-BR')}
                    </Text>
                  )}
                </View>
                <TouchableOpacity
                  style={styles.disconnectBtn}
                  onPress={() => handleDisconnect(item)}
                >
                  <Text style={styles.disconnectBtnText}>Remover</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}
      </Card>

      {/* Connect Button */}
      <TouchableOpacity
        style={[styles.connectBtn, isLoading && styles.connectBtnDisabled]}
        onPress={handleConnect}
        disabled={isLoading}
      >
        {isLoading ? (
          <Text style={styles.connectBtnText}>Abrindo Pluggy Connect...</Text>
        ) : (
          <Text style={styles.connectBtnText}>🏦 Conectar Nova Instituição</Text>
        )}
      </TouchableOpacity>

      {/* Setup Instructions */}
      <Card style={styles.setupCard}>
        <Text style={styles.setupTitle}>⚙️ Primeira vez usando?</Text>
        <Text style={styles.setupText}>
          Para conectar suas contas você precisa de credenciais Pluggy (Client ID e Secret).
          {'\n\n'}1. Crie sua conta gratuita em pluggy.ai
          {'\n'}2. Obtenha seu Client ID e Client Secret
          {'\n'}3. Configure em Configurações → API Keys
        </Text>
        <TouchableOpacity
          onPress={() => router.push('/settings')}
          style={styles.setupBtn}
        >
          <Text style={styles.setupBtnText}>Ir para Configurações</Text>
        </TouchableOpacity>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xl },
  title: { color: Colors.text, fontSize: FontSize.xxl, fontWeight: '800' },
  subtitle: { color: Colors.textMuted, fontSize: FontSize.sm },
  securityCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
    borderColor: Colors.success,
    backgroundColor: Colors.successBg,
  },
  securityIcon: { fontSize: 24 },
  securityTitle: { color: Colors.success, fontSize: FontSize.sm, fontWeight: '700' },
  securityDesc: { color: Colors.text, fontSize: FontSize.xs, lineHeight: 18, marginTop: 4 },
  institutionsList: { flexDirection: 'row', gap: Spacing.sm, paddingBottom: Spacing.xs },
  institutionChip: {
    alignItems: 'center',
    backgroundColor: Colors.bgCardHover,
    borderRadius: Radius.md,
    padding: Spacing.sm,
    minWidth: 70,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  institutionLogo: { fontSize: 24, marginBottom: 4 },
  institutionName: { color: Colors.textSecondary, fontSize: FontSize.xs, fontWeight: '600' },
  moreText: { color: Colors.textMuted, fontSize: FontSize.xs, textAlign: 'center', marginTop: Spacing.sm },
  noConnectionsText: { color: Colors.textMuted, fontSize: FontSize.sm, textAlign: 'center', padding: Spacing.md },
  itemsList: { gap: Spacing.sm },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  itemInfo: { flex: 1, gap: 4 },
  itemName: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '700' },
  itemStatus: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  statusLabel: { fontSize: FontSize.xs, fontWeight: '600' },
  lastUpdate: { color: Colors.textMuted, fontSize: FontSize.xs },
  disconnectBtn: {
    backgroundColor: Colors.dangerBg,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.danger,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
  },
  disconnectBtnText: { color: Colors.danger, fontSize: FontSize.xs, fontWeight: '700' },
  connectBtn: {
    backgroundColor: Colors.accent,
    borderRadius: Radius.md,
    padding: Spacing.md + 4,
    alignItems: 'center',
  },
  connectBtnDisabled: { opacity: 0.5 },
  connectBtnText: { color: '#fff', fontSize: FontSize.md, fontWeight: '800' },
  setupCard: { borderColor: Colors.border, gap: Spacing.sm },
  setupTitle: { color: Colors.text, fontSize: FontSize.sm, fontWeight: '700' },
  setupText: { color: Colors.textSecondary, fontSize: FontSize.sm, lineHeight: 22 },
  setupBtn: {
    backgroundColor: Colors.bgCardHover,
    borderRadius: Radius.sm,
    padding: Spacing.sm,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  setupBtnText: { color: Colors.accent, fontSize: FontSize.sm, fontWeight: '600' },
});
