import { Tabs } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Colors } from '../../src/constants/colors';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          backgroundColor: Colors.bgCard,
          borderTopColor: Colors.border,
          borderTopWidth: 1,
          height: 60,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarActiveTintColor: Colors.accent,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '600',
        },
        headerStyle: { backgroundColor: Colors.bg },
        headerTintColor: Colors.text,
        headerShadowVisible: false,
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="view-dashboard" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="projections"
        options={{
          title: 'Projeções',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="chart-line" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="portfolio"
        options={{
          title: 'Carteira',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="briefcase-variant" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="finances"
        options={{
          title: 'Finanças',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="bank" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="market"
        options={{
          title: 'Mercado',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="trending-up" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="ai-advisor"
        options={{
          title: 'IA Advisor',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="robot-excited" color={color} size={size} />
          ),
        }}
      />
    </Tabs>
  );
}
