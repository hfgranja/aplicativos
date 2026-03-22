import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Colors } from '../src/constants/colors';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: Colors.bg }}>
      <StatusBar style="light" backgroundColor={Colors.bg} />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: Colors.bg },
          headerTintColor: Colors.text,
          headerShadowVisible: false,
          contentStyle: { backgroundColor: Colors.bg },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="modal/trade"
          options={{ presentation: 'modal', title: 'Simular Trade', headerStyle: { backgroundColor: Colors.bgCard } }}
        />
        <Stack.Screen
          name="modal/connect-bank"
          options={{ presentation: 'modal', title: 'Conectar Banco', headerStyle: { backgroundColor: Colors.bgCard } }}
        />
        <Stack.Screen
          name="modal/ir-advisor"
          options={{ presentation: 'modal', title: 'Imposto de Renda', headerStyle: { backgroundColor: Colors.bgCard } }}
        />
        <Stack.Screen
          name="modal/strategy"
          options={{ presentation: 'modal', title: 'Estratégia', headerStyle: { backgroundColor: Colors.bgCard } }}
        />
        <Stack.Screen
          name="settings"
          options={{ title: 'Configurações', headerStyle: { backgroundColor: Colors.bg } }}
        />
      </Stack>
    </GestureHandlerRootView>
  );
}
