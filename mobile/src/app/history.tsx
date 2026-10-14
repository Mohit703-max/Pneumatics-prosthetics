/**
 * History screen — list of persisted predictions from PostgreSQL.
 */
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { BottomTabInset, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import type { PredictionHistoryItem } from '@/lib/api';
import { api } from '@/lib/api';
import { formatConfidence } from '@/lib/emg';

const PAGE_SIZE = 20;

export default function HistoryScreen() {
  const insets = useSafeAreaInsets();
  const theme = useTheme();

  const [items, setItems] = useState<PredictionHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = async (reset = false) => {
    try {
      setError(null);
      const offset = reset ? 0 : items.length;
      const res = await api.listPredictions(PAGE_SIZE, offset);
      setTotal(res.total);
      setItems(reset ? res.items : [...items, ...res.items]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load history');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { load(true); }, []);

  const renderItem = ({ item }: { item: PredictionHistoryItem }) => {
    const date = new Date(item.created_at);
    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const dateStr = date.toLocaleDateString([], { month: 'short', day: 'numeric' });

    return (
      <ThemedView type="backgroundElement" style={styles.row}>
        <View style={styles.rowLeft}>
          <ThemedText type="small">
            {item.predicted_display_name ?? item.predicted_code}
          </ThemedText>
          <ThemedText type="code" themeColor="textSecondary">{item.predicted_code}</ThemedText>
        </View>
        <View style={styles.rowRight}>
          <View style={styles.metaRow}>
            <ThemedText
              type="code"
              style={{
                color: item.inference_mode === 'model' ? '#34C759' : '#FF9500',
                fontSize: 10,
              }}>
              {item.inference_mode}
            </ThemedText>
            <ThemedText type="code" themeColor="textSecondary" style={styles.conf}>
              {formatConfidence(item.confidence)}
            </ThemedText>
          </View>
          <ThemedText type="code" themeColor="textSecondary" style={styles.dateText}>
            {dateStr} {timeStr}
          </ThemedText>
        </View>
      </ThemedView>
    );
  };

  if (loading) {
    return (
      <ThemedView style={[styles.center, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" />
      </ThemedView>
    );
  }

  return (
    <FlatList
      style={{ backgroundColor: theme.background }}
      contentContainerStyle={[
        styles.list,
        {
          paddingTop: insets.top + Spacing.three,
          paddingBottom: insets.bottom + BottomTabInset + Spacing.three,
        },
      ]}
      data={items}
      keyExtractor={(item) => String(item.prediction_id)}
      renderItem={renderItem}
      ItemSeparatorComponent={() => <View style={styles.separator} />}
      ListHeaderComponent={() => (
        <View style={styles.header}>
          <ThemedText type="subtitle">Prediction History</ThemedText>
          <ThemedText type="small" themeColor="textSecondary">
            {total} record{total !== 1 ? 's' : ''} stored
          </ThemedText>
        </View>
      )}
      ListEmptyComponent={() => (
        <ThemedView type="backgroundElement" style={styles.empty}>
          <ThemedText themeColor="textSecondary" type="small">
            No predictions yet. Go to Predict to run your first inference.
          </ThemedText>
        </ThemedView>
      )}
      ListFooterComponent={() =>
        items.length < total ? (
          <Pressable
            style={({ pressed }) => [styles.loadMore, { opacity: pressed ? 0.7 : 1 }]}
            onPress={() => load()}>
            <ThemedText type="small" style={styles.loadMoreText}>
              Load more
            </ThemedText>
          </Pressable>
        ) : null
      }
      onRefresh={() => { setRefreshing(true); load(true); }}
      refreshing={refreshing}
      ListFooterComponentStyle={{ padding: Spacing.three }}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  list: { paddingHorizontal: Spacing.three, gap: Spacing.two },
  header: { marginBottom: Spacing.three, gap: Spacing.one },
  row: {
    borderRadius: Spacing.two,
    padding: Spacing.three,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rowLeft: { gap: 2, flex: 1 },
  rowRight: { alignItems: 'flex-end', gap: 2 },
  metaRow: { flexDirection: 'row', gap: Spacing.two, alignItems: 'center' },
  conf: { fontSize: 10 },
  dateText: { fontSize: 10 },
  separator: { height: Spacing.one },
  empty: { borderRadius: Spacing.three, padding: Spacing.four, alignItems: 'center' },
  loadMore: {
    alignItems: 'center',
    padding: Spacing.three,
    backgroundColor: '#3c87f730',
    borderRadius: Spacing.two,
  },
  loadMoreText: { color: '#3c87f7' },
});
