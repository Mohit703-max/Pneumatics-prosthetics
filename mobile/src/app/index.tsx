/**
 * Dashboard screen — system status, gesture registry, quick navigation.
 */
import { useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { BottomTabInset, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import type { Gesture, HealthResponse } from '@/lib/api';
import { api } from '@/lib/api';

type StatusDot = 'ok' | 'warn' | 'error' | 'loading';

function StatusBadge({ status, label }: { status: StatusDot; label: string }) {
  const theme = useTheme();
  const colors: Record<StatusDot, string> = {
    ok: '#34C759',
    warn: '#FF9500',
    error: '#FF3B30',
    loading: theme.textSecondary,
  };
  return (
    <View style={styles.badgeRow}>
      <View style={[styles.dot, { backgroundColor: colors[status] }]} />
      <ThemedText type="small">{label}</ThemedText>
    </View>
  );
}

export default function DashboardScreen() {
  const insets = useSafeAreaInsets();
  const theme = useTheme();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [gestures, setGestures] = useState<Gesture[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      setError(null);
      const [h, g] = await Promise.all([api.health(), api.listGestures()]);
      setHealth(h);
      setGestures(g);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection failed');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { load(); }, []);

  const dbStatus: StatusDot = !health ? 'loading' : health.database === 'ok' ? 'ok' : 'error';
  const mlStatus: StatusDot = !health
    ? 'loading'
    : health.ml.status === 'model_loaded'
    ? 'ok'
    : 'warn';

  return (
    <ScrollView
      style={[styles.scroll, { backgroundColor: theme.background }]}
      contentContainerStyle={[
        styles.container,
        { paddingTop: insets.top + Spacing.four, paddingBottom: insets.bottom + BottomTabInset + Spacing.four },
      ]}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}>

      <ThemedText type="title" style={styles.title}>HASTRA</ThemedText>
      <ThemedText themeColor="textSecondary" style={styles.subtitle}>
        EMG Hand Gesture Recognition
      </ThemedText>

      {/* System status */}
      <ThemedView type="backgroundElement" style={styles.card}>
        <ThemedText type="smallBold" style={styles.cardTitle}>System Status</ThemedText>
        {loading ? (
          <ActivityIndicator />
        ) : error ? (
          <StatusBadge status="error" label={`Backend unreachable — ${error}`} />
        ) : (
          <>
            <StatusBadge
              status={dbStatus}
              label={`Database: ${health?.database === 'ok' ? 'connected' : health?.database_error ?? 'error'}`}
            />
            <StatusBadge
              status={mlStatus}
              label={
                health?.ml.status === 'model_loaded'
                  ? `Model loaded (${health.ml.model_classes.length} classes)`
                  : 'ML: fallback active — no trained model'
              }
            />
          </>
        )}
      </ThemedView>

      {/* Gesture registry */}
      {gestures.length > 0 && (
        <ThemedView type="backgroundElement" style={styles.card}>
          <ThemedText type="smallBold" style={styles.cardTitle}>Gesture Registry</ThemedText>
          {gestures.map((g) => (
            <View key={g.code} style={styles.gestureRow}>
              <View style={styles.gestureLeft}>
                <ThemedText type="small">{g.display_name}</ThemedText>
                <ThemedText type="code" themeColor="textSecondary">{g.code}</ThemedText>
              </View>
              <View style={[
                styles.supportBadge,
                { backgroundColor: g.model_supported ? '#34C75930' : '#FF950030' },
              ]}>
                <ThemedText
                  type="code"
                  style={{ color: g.model_supported ? '#34C759' : '#FF9500', fontSize: 10 }}>
                  {g.model_supported ? 'ML ready' : 'No model'}
                </ThemedText>
              </View>
            </View>
          ))}
        </ThemedView>
      )}

      {/* Info footer */}
      <ThemedView type="backgroundElement" style={styles.card}>
        <ThemedText type="small" themeColor="textSecondary">
          Use the Predict tab to submit an EMG window and the History tab to review past results.
        </ThemedText>
      </ThemedView>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1 },
  container: { paddingHorizontal: Spacing.four, gap: Spacing.three },
  title: { textAlign: 'center' },
  subtitle: { textAlign: 'center', marginBottom: Spacing.two },
  card: { borderRadius: Spacing.three, padding: Spacing.three, gap: Spacing.two },
  cardTitle: { marginBottom: Spacing.one },
  badgeRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.two },
  dot: { width: 8, height: 8, borderRadius: 4 },
  gestureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: Spacing.one,
  },
  gestureLeft: { gap: 2 },
  supportBadge: {
    paddingHorizontal: Spacing.two,
    paddingVertical: 2,
    borderRadius: Spacing.two,
  },
});
