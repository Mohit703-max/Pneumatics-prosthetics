/**
 * Predict screen — generate / select an EMG window, submit to backend, show result.
 */
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { BottomTabInset, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import type { PredictResponse } from '@/lib/api';
import { api } from '@/lib/api';
import { channelRms, formatConfidence, generateDemoWindow } from '@/lib/emg';

type Stage = 'idle' | 'ready' | 'loading' | 'result' | 'error';

export default function PredictScreen() {
  const insets = useSafeAreaInsets();
  const theme = useTheme();

  const [stage, setStage] = useState<Stage>('idle');
  const [emgWindow, setEmgWindow] = useState<number[][] | null>(null);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleGenerate = () => {
    const window = generateDemoWindow();
    setEmgWindow(window);
    setResult(null);
    setErrorMsg(null);
    setStage('ready');
  };

  const handlePredict = async () => {
    if (!emgWindow) return;
    setStage('loading');
    setErrorMsg(null);
    try {
      const res = await api.predict({ raw_emg: emgWindow });
      setResult(res);
      setStage('result');
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : 'Unknown error');
      setStage('error');
    }
  };

  const rms = emgWindow ? channelRms(emgWindow) : null;
  const maxRms = rms ? Math.max(...rms) : 1;

  return (
    <ScrollView
      style={[styles.scroll, { backgroundColor: theme.background }]}
      contentContainerStyle={[
        styles.container,
        { paddingTop: insets.top + Spacing.four, paddingBottom: insets.bottom + BottomTabInset + Spacing.four },
      ]}>

      <ThemedText type="subtitle" style={styles.heading}>Gesture Prediction</ThemedText>

      {/* Step 1 — Generate window */}
      <ThemedView type="backgroundElement" style={styles.card}>
        <ThemedText type="smallBold">Step 1 — EMG Window</ThemedText>
        <ThemedText type="small" themeColor="textSecondary" style={styles.note}>
          No hardware connected. Generate a synthetic demo window for end-to-end testing.
          Results will be labelled FALLBACK until a real model is loaded.
        </ThemedText>

        <Pressable
          style={({ pressed }) => [styles.btn, { opacity: pressed ? 0.7 : 1 }]}
          onPress={handleGenerate}>
          <ThemedText type="small" style={styles.btnText}>Generate Demo Window</ThemedText>
        </Pressable>
      </ThemedView>

      {/* Signal preview */}
      {rms && (
        <ThemedView type="backgroundElement" style={styles.card}>
          <ThemedText type="smallBold">Signal Preview — Channel RMS</ThemedText>
          <View style={styles.barChart}>
            {rms.map((v, i) => (
              <View key={i} style={styles.barCol}>
                <View
                  style={[
                    styles.bar,
                    {
                      height: Math.max(4, (v / maxRms) * 80),
                      backgroundColor: theme.text,
                    },
                  ]}
                />
                <ThemedText type="code" style={styles.barLabel}>
                  {i + 1}
                </ThemedText>
              </View>
            ))}
          </View>
          <ThemedText type="code" themeColor="textSecondary" style={styles.note}>
            Synthetic data — 10 channels × 200 samples
          </ThemedText>
        </ThemedView>
      )}

      {/* Step 2 — Submit */}
      {stage !== 'idle' && (
        <ThemedView type="backgroundElement" style={styles.card}>
          <ThemedText type="smallBold">Step 2 — Run Prediction</ThemedText>
          <Pressable
            style={({ pressed }) => [
              styles.btn,
              styles.btnPrimary,
              { opacity: pressed ? 0.7 : 1 },
            ]}
            onPress={handlePredict}
            disabled={stage === 'loading'}>
            <ThemedText type="small" style={styles.btnText}>
              Submit to Backend
            </ThemedText>
          </Pressable>
          {stage === 'loading' && <ActivityIndicator style={{ marginTop: Spacing.two }} />}
        </ThemedView>
      )}

      {/* Result */}
      {stage === 'result' && result && (
        <ThemedView type="backgroundElement" style={styles.card}>
          <ThemedText type="smallBold">Result</ThemedText>

          {/* Fallback warning — always shown when mode is fallback */}
          {result.inference_mode === 'fallback' && (
            <View style={styles.fallbackBanner}>
              <ThemedText type="code" style={styles.fallbackText}>
                ⚠ FALLBACK MODE — No trained model loaded. This result is a heuristic estimate only.
              </ThemedText>
            </View>
          )}

          <View style={styles.resultRow}>
            <ThemedText themeColor="textSecondary" type="small">Gesture</ThemedText>
            <ThemedText type="subtitle">
              {result.predicted_display_name ?? result.predicted_code}
            </ThemedText>
          </View>
          <View style={styles.resultRow}>
            <ThemedText themeColor="textSecondary" type="small">Code</ThemedText>
            <ThemedText type="code">{result.predicted_code}</ThemedText>
          </View>
          <View style={styles.resultRow}>
            <ThemedText themeColor="textSecondary" type="small">Confidence</ThemedText>
            <ThemedText type="small">{formatConfidence(result.confidence)}</ThemedText>
          </View>
          <View style={styles.resultRow}>
            <ThemedText themeColor="textSecondary" type="small">Mode</ThemedText>
            <ThemedText
              type="code"
              style={{
                color: result.inference_mode === 'model' ? '#34C759' : '#FF9500',
              }}>
              {result.inference_mode}
            </ThemedText>
          </View>
          <View style={styles.resultRow}>
            <ThemedText themeColor="textSecondary" type="small">Prediction ID</ThemedText>
            <ThemedText type="code">#{result.prediction_id}</ThemedText>
          </View>
        </ThemedView>
      )}

      {/* Error */}
      {stage === 'error' && errorMsg && (
        <ThemedView type="backgroundElement" style={styles.card}>
          <ThemedText type="small" style={{ color: '#FF3B30' }}>
            Error: {errorMsg}
          </ThemedText>
        </ThemedView>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1 },
  container: { paddingHorizontal: Spacing.four, gap: Spacing.three },
  heading: { textAlign: 'center', marginBottom: Spacing.two },
  card: { borderRadius: Spacing.three, padding: Spacing.three, gap: Spacing.two },
  note: { lineHeight: 18 },
  btn: {
    backgroundColor: '#3c87f7',
    borderRadius: Spacing.two,
    paddingVertical: Spacing.two,
    paddingHorizontal: Spacing.three,
    alignItems: 'center',
  },
  btnPrimary: { backgroundColor: '#208AEF' },
  btnText: { color: '#ffffff' },
  barChart: { flexDirection: 'row', alignItems: 'flex-end', gap: 4, height: 100 },
  barCol: { flex: 1, alignItems: 'center', gap: 2 },
  bar: { width: '100%', borderRadius: 2 },
  barLabel: { fontSize: 9 },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 2,
  },
  fallbackBanner: {
    backgroundColor: '#FF950020',
    borderRadius: Spacing.two,
    padding: Spacing.two,
  },
  fallbackText: { color: '#FF9500', lineHeight: 16 },
});
